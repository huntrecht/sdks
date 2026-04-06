"""
GraphQL resolvers for credit history queries and mutations
"""
from typing import List, Optional
from datetime import datetime
import psycopg2.extras
from oauth_auth import get_db_connection
from sdk.python.credit_history_types import (
    CreditTransaction,
    CreditHistoryConnection,
    CreditHistoryEdge,
    PageInfo,
    CreditHistoryInput,
    IngestResult,
    CreditHistoryRecord
)
from sdk.python.shopify_company_registry import ShopifyCompanyRegistry
from sdk.python.credit_history_rag_loader import CreditHistoryRAGLoader
from sdk.python.data_provider_connector import DataProviderRegistry
from sdk.python.external_db_connectors import ConnectorError
from shopify_client import ShopifyAdminClient
import hashlib
from cryptography.fernet import Fernet
import os
import base64


def get_encryption_key():
    """
    Get encryption key for sensitive data (REQUIRED for production)
    
    The key must be a 32-byte URL-safe base64-encoded string (44 characters).
    Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    
    Set as environment variable: CREDIT_HISTORY_ENCRYPTION_KEY=<your-key-here>
    
    ⚠️  CRITICAL: The same key MUST be used across all server restarts to decrypt
    existing data. Loss of this key means permanent data loss.
    """
    key = os.getenv("CREDIT_HISTORY_ENCRYPTION_KEY")
    
    if not key:
        raise ValueError(
            "❌ CREDIT_HISTORY_ENCRYPTION_KEY environment variable is required!\n\n"
            "To generate a secure key, run:\n"
            "  python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"\n\n"
            "Then set it as an environment variable:\n"
            "  export CREDIT_HISTORY_ENCRYPTION_KEY=<your-generated-key>\n\n"
            "⚠️  IMPORTANT: Store this key securely and use the SAME key across all restarts!"
        )
    
    # Validate key format (should be 44 characters for URL-safe base64 of 32 bytes)
    if len(key) != 44:
        raise ValueError(
            f"❌ Invalid CREDIT_HISTORY_ENCRYPTION_KEY length: {len(key)} (expected 44 characters)\n"
            "Generate a proper key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    
    return key


# Initialize Fernet with the required encryption key (FAIL FAST if not set)
FERNET = Fernet(get_encryption_key().encode())
print("✅ Credit history encryption initialized successfully")


def encrypt_field(value: Optional[str]) -> Optional[str]:
    """Encrypt sensitive field data"""
    if not value:
        return None
    
    return FERNET.encrypt(value.encode()).decode()


def decrypt_field(encrypted_value: Optional[str]) -> Optional[str]:
    """Decrypt sensitive field data"""
    if not encrypted_value:
        return None
    
    try:
        return FERNET.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        print(f"⚠️  Decryption failed (key mismatch or corrupt data): {e}")
        return None


def mask_account_number(account_number: Optional[str]) -> Optional[str]:
    """Mask sensitive account number - show only last 4 digits"""
    if not account_number:
        return None
    
    # Decrypt if encrypted
    decrypted = decrypt_field(account_number)
    if decrypted:
        account_number = decrypted
    
    if len(account_number) <= 4:
        return "****"
    return f"****{account_number[-4:]}"


def sanitize_for_rag(text: str) -> str:
    """Remove or mask sensitive data before adding to RAG pipeline"""
    # Replace account numbers with masked version
    import re
    # Mask potential account numbers (sequences of 8+ digits)
    text = re.sub(r'\b\d{8,}\b', '****', text)
    # Mask email addresses
    text = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '****@****.***', text)
    return text


class CreditHistoryResolver:
    """Resolvers for credit history GraphQL queries and mutations"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection or get_db_connection()
        self.admin_client = ShopifyAdminClient()
        self.company_registry = ShopifyCompanyRegistry(self.admin_client, self.db)
        self.rag_loader = CreditHistoryRAGLoader(self.db)
        self.provider_registry = DataProviderRegistry()
        self._owns_db = db_connection is None
    
    def close(self):
        """Close database connection if owned by resolver"""
        if self._owns_db and self.db:
            self.db.close()
    
    def get_credit_history(
        self,
        company_id: str,
        shopify_company_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> CreditHistoryConnection:
        """Get paginated credit history for a company with cursor-based pagination"""
        cursor_db = self.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        try:
            # Build query with filters
            conditions = []
            params = []
            
            if shopify_company_id:
                conditions.append("shopify_company_id = %s")
                params.append(shopify_company_id)
            else:
                conditions.append("company_id = %s")
                params.append(company_id)
            
            if start_date:
                conditions.append("transaction_date >= %s")
                params.append(start_date)
            
            if end_date:
                conditions.append("transaction_date <= %s")
                params.append(end_date)
            
            # Decode cursor for pagination (format: "timestamp_id")
            if cursor:
                try:
                    cursor_parts = cursor.split("_")
                    if len(cursor_parts) == 2:
                        cursor_date = cursor_parts[0]
                        cursor_id = int(cursor_parts[1])
                        # Use keyset pagination: only fetch records before this cursor
                        conditions.append("(transaction_date < %s OR (transaction_date = %s AND id < %s))")
                        params.extend([cursor_date, cursor_date, cursor_id])
                except (ValueError, IndexError):
                    print(f"⚠️  Invalid cursor format: {cursor}")
            
            where_clause = " AND ".join(conditions)
            
            # Get total count
            count_conditions = [c for c in conditions if not c.startswith("(transaction_date <")]
            count_where = " AND ".join(count_conditions) if count_conditions else "1=1"
            count_params = params[:len(count_conditions)]
            
            cursor_db.execute(f"""
                SELECT COUNT(*) as total
                FROM credit_history
                WHERE {count_where}
            """, count_params)
            total_count = cursor_db.fetchone()["total"]
            
            # Get records with pagination (fetch limit + 1 to detect next page)
            pagination_params = params.copy()
            pagination_params.append(limit + 1)
            
            cursor_db.execute(f"""
                SELECT *
                FROM credit_history
                WHERE {where_clause}
                ORDER BY transaction_date DESC, id DESC
                LIMIT %s
            """, pagination_params)
            
            rows = cursor_db.fetchall()
            has_next_page = len(rows) > limit
            records = rows[:limit]
            
            # Create edges with decrypted and masked sensitive data
            edges = []
            for row in records:
                # Decrypt email for display (or mask)
                decrypted_email = decrypt_field(row["email"])
                masked_email = f"****@{decrypted_email.split('@')[1]}" if decrypted_email and '@' in decrypted_email else "****@****.***"
                
                transaction = CreditTransaction(
                    id=str(row["id"]),
                    company_id=row["company_id"],
                    email=masked_email,
                    date=row["transaction_date"],
                    reference=row["reference"],
                    inflow=float(row["inflow"]) if row["inflow"] else None,
                    outflow=float(row["outflow"]) if row["outflow"] else None,
                    balance=float(row["balance"]) if row.get("balance") is not None else None,
                    account_name=row["account_name"],
                    account_number=mask_account_number(row["account_number"]),
                    bank=row["bank"],
                    currency=row["currency"],
                    shopify_company_id=row["shopify_company_id"],
                    provider_id=row["provider_id"]
                )
                
                edge = CreditHistoryEdge(
                    node=transaction,
                    cursor=f"{row['transaction_date']}_{row['id']}"
                )
                edges.append(edge)
            
            # Create page info
            page_info = PageInfo(
                has_next_page=has_next_page,
                end_cursor=edges[-1].cursor if edges else None
            )
            
            return CreditHistoryConnection(
                edges=edges,
                page_info=page_info,
                total_count=total_count
            )
            
        finally:
            cursor_db.close()
    
    def get_company_summary(self, shopify_company_id: str) -> dict:
        """Get aggregated credit history summary"""
        return self.rag_loader.get_credit_summary(shopify_company_id)
    
    async def ingest_records(
        self,
        provider_id: str,
        company_id: str,
        records: List[CreditHistoryInput],
        enrich_shopify: bool = True
    ) -> IngestResult:
        """Ingest credit history records with Shopify enrichment"""
        errors = []
        enriched_count = 0
        companies_created = 0
        
        try:
            # Convert inputs to records
            credit_records = []
            for input_record in records:
                record = CreditHistoryRecord(
                    company_id=input_record.company_id,
                    email=input_record.email,
                    date=input_record.date,
                    reference=input_record.reference,
                    inflow=input_record.inflow,
                    outflow=input_record.outflow,
                    balance=input_record.balance,
                    account_name=input_record.account_name,
                    account_number=input_record.account_number,
                    bank=input_record.bank,
                    currency=input_record.currency or "USD",
                    provider_id=provider_id,
                    metadata=input_record.metadata
                )
                credit_records.append(record)
            
            # Enrich with Shopify company IDs
            if enrich_shopify:
                for record in credit_records:
                    try:
                        shopify_id = await self.company_registry.get_or_create_company(
                            external_company_id=record.company_id,
                            email=record.email,
                            company_name=record.account_name
                        )
                        record.shopify_company_id = shopify_id
                        enriched_count += 1
                        
                        # Check if company was newly created
                        if "newly_created" in str(shopify_id):
                            companies_created += 1
                            
                    except Exception as e:
                        errors.append(f"Failed to enrich {record.company_id}: {str(e)}")
            
            # Store in database
            stored_count = self.rag_loader.store_records(credit_records)
            
            # Create RAG documents
            documents = self.rag_loader.create_documents(credit_records)
            print(f"✅ Created {len(documents)} RAG documents for ingestion")
            
            return IngestResult(
                success=len(errors) == 0,
                records_processed=stored_count,
                records_enriched=enriched_count,
                shopify_companies_created=companies_created,
                errors=errors
            )
            
        except Exception as e:
            errors.append(f"Ingestion failed: {str(e)}")
            return IngestResult(
                success=False,
                records_processed=0,
                records_enriched=0,
                shopify_companies_created=0,
                errors=errors
            )
    
    async def trigger_sync(
        self,
        provider_id: str,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> IngestResult:
        """
        Trigger automatic sync from external database (UPDATED with real connectors)
        
        Fetches credit history from external MySQL, MongoDB, Oracle, PostgreSQL, or GraphQL API
        based on provider configuration from Data Connect UI
        """
        errors = []
        
        try:
            print(f"🔄 Triggering provider sync: {provider_id} for company {company_id}")
            
            # Reload providers to get latest configs from database
            self.provider_registry.reload_providers()
            
            # Get provider connector (real database connector)
            connector = self.provider_registry.get_provider(provider_id)
            if not connector:
                available_providers = self.provider_registry.list_providers()
                error_msg = f"Provider {provider_id} not found. Available: {available_providers}"
                print(f"❌ {error_msg}")
                return IngestResult(
                    success=False,
                    records_processed=0,
                    records_enriched=0,
                    shopify_companies_created=0,
                    errors=[error_msg]
                )
            
            # Fetch credit history from external database
            print(f"📡 Fetching from external {connector.connector_type} database...")
            
            # Test connection first to ensure provider is accessible
            connection_ok = await connector.test_connection()
            if not connection_ok:
                error_msg = f"Failed to connect to provider {provider_id}. Check credentials and network connectivity."
                print(f"❌ {error_msg}")
                return IngestResult(
                    success=False,
                    records_processed=0,
                    records_enriched=0,
                    shopify_companies_created=0,
                    errors=[error_msg]
                )
            
            raw_records = await connector.fetch_credit_history(
                company_id=company_id,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )
            
            if not raw_records:
                # Empty result could mean: no records, OR fetch failed silently
                # Log warning but don't fail the sync (could be legitimate no-data scenario)
                print(f"⚠️  No records returned for company {company_id}. This could mean:")
                print(f"   - Company has no credit history in the specified date range")
                print(f"   - Company ID '{company_id}' doesn't exist in external database")
                print(f"   - Fetch operation failed silently (check connector logs above)")
                return IngestResult(
                    success=True,
                    records_processed=0,
                    records_enriched=0,
                    shopify_companies_created=0,
                    errors=[]
                )
            
            print(f"✅ Fetched {len(raw_records)} records from external database")
            
            # Convert to input records (transform external format to standard format)
            input_records = []
            for raw in raw_records:
                # Handle date conversion
                record_date = raw.get("date")
                if isinstance(record_date, str):
                    record_date = datetime.fromisoformat(record_date.replace('Z', '+00:00'))
                
                input_record = CreditHistoryInput(
                    company_id=raw.get("company_id", company_id),
                    email=raw.get("email"),
                    date=record_date,
                    reference=raw.get("reference"),
                    inflow=float(raw.get("inflow", 0.0)),
                    outflow=float(raw.get("outflow", 0.0)),
                    balance=float(raw.get("balance")) if raw.get("balance") is not None else None,
                    account_name=raw.get("account_name"),
                    account_number=raw.get("account_number"),
                    bank=raw.get("bank"),
                    currency=raw.get("currency", "USD"),
                    provider_id=provider_id,
                    metadata=None
                )
                input_records.append(input_record)
            
            print(f"✅ Transformed {len(input_records)} records to standard format")
            
            # Ingest the records (encrypt PII, enrich with Shopify, load to RAG)
            return await self.ingest_records(
                provider_id=provider_id,
                company_id=company_id,
                records=input_records,
                enrich_shopify=True
            )
            
        except Exception as e:
            # Check if it's a connector-related error
            if isinstance(e, ConnectorError):
                # Database/connector failure (connection, auth, query, network)
                error_msg = f"External database connector failed: {str(e)}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                return IngestResult(
                    success=False,
                    records_processed=0,
                    records_enriched=0,
                    shopify_companies_created=0,
                    errors=errors
                )
            else:
                # Unexpected error (code bugs, logic errors)
                import traceback
                error_msg = f"Provider sync failed unexpectedly: {str(e)}"
                print(f"❌ {error_msg}")
                print(f"Stack trace: {traceback.format_exc()}")
                errors.append(error_msg)
                return IngestResult(
                    success=False,
                    records_processed=0,
                    records_enriched=0,
                    shopify_companies_created=0,
                    errors=errors
                )
