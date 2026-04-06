"""
Credit History RAG Loader
Loads credit history data into LangChain/ChromaDB for RAG pipeline
"""
from typing import List, Dict, Any
from datetime import datetime
import psycopg2.extras
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sdk.python.credit_history_types import CreditHistoryRecord


class CreditHistoryRAGLoader:
    """Loader for ingesting credit history into RAG pipeline"""
    
    def __init__(self, db_connection, embedding_function=None):
        self.db_connection = db_connection
        self.embedding_function = embedding_function
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def store_records(self, records: List[CreditHistoryRecord]) -> int:
        """Store credit history records in PostgreSQL with encryption"""
        from sdk.python.credit_history_resolvers import encrypt_field
        
        cursor = self.db_connection.cursor()
        stored_count = 0
        
        try:
            for record in records:
                # Encrypt sensitive fields before storage
                encrypted_email = encrypt_field(record.email)
                encrypted_account_number = encrypt_field(record.account_number) if record.account_number else None
                
                cursor.execute("""
                    INSERT INTO credit_history (
                        company_id,
                        shopify_company_id,
                        email,
                        transaction_date,
                        inflow,
                        outflow,
                        balance,
                        reference,
                        account_name,
                        account_number,
                        bank,
                        currency,
                        provider_id,
                        metadata,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (provider_id, company_id, transaction_date, reference)
                    DO UPDATE SET
                        inflow = EXCLUDED.inflow,
                        outflow = EXCLUDED.outflow,
                        balance = EXCLUDED.balance,
                        updated_at = NOW()
                    RETURNING id
                """, (
                    record.company_id,
                    record.shopify_company_id,
                    encrypted_email,
                    record.date,
                    record.inflow or 0,
                    record.outflow or 0,
                    record.balance,
                    record.reference,
                    record.account_name,
                    encrypted_account_number,
                    record.bank,
                    record.currency,
                    record.provider_id,
                    record.metadata
                ))
                
                stored_count += 1
            
            self.db_connection.commit()
            print(f"✅ Stored {stored_count} encrypted credit history records in database")
            return stored_count
            
        except Exception as e:
            self.db_connection.rollback()
            print(f"❌ Error storing records: {e}")
            raise
        finally:
            cursor.close()
    
    def create_documents(self, records: List[CreditHistoryRecord]) -> List[Document]:
        """Convert credit history records to LangChain documents for RAG (PII-free)"""
        documents = []
        
        for record in records:
            # Create rich text representation of credit transaction (already sanitized)
            content = self._format_transaction_text(record)
            
            # Create metadata for filtering and retrieval (NO PII)
            metadata = {
                "company_id": record.company_id,
                "shopify_company_id": record.shopify_company_id,
                # NO email - PII removed
                "date": record.date.isoformat(),
                "bank": record.bank,
                "currency": record.currency,
                "provider_id": record.provider_id,
                "transaction_type": "inflow" if (record.inflow or 0) > 0 else "outflow",
                "amount": (record.inflow or 0) - (record.outflow or 0)
                # NO account_number - PII removed
            }
            
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
        
        print(f"✅ Created {len(documents)} PII-free RAG documents from credit history")
        return documents
    
    def _format_transaction_text(self, record: CreditHistoryRecord) -> str:
        """Format credit transaction as readable text for RAG (with PII sanitized)"""
        from sdk.python.credit_history_resolvers import sanitize_for_rag
        
        # Create text with masked sensitive data
        lines = [
            f"Company: {record.company_id}",
            f"Email: ****@****.***",  # Masked email
            f"Date: {record.date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Bank: {record.bank or 'N/A'}",
            f"Account: {record.account_name or 'N/A'} (****)",  # Masked account number
            f"Currency: {record.currency}",
            ""
        ]
        
        if record.inflow and record.inflow > 0:
            lines.append(f"CREDIT (Inflow): {record.currency} {record.inflow:,.2f}")
        
        if record.outflow and record.outflow > 0:
            lines.append(f"DEBIT (Outflow): {record.currency} {record.outflow:,.2f}")
        
        if record.balance is not None:
            lines.append(f"Running Balance: {record.currency} {record.balance:,.2f}")
        
        # Sanitize reference text
        reference = sanitize_for_rag(record.reference)
        lines.append(f"Reference: {reference}")
        
        return "\n".join(lines)
    
    def get_credit_summary(self, shopify_company_id: str) -> Dict[str, Any]:
        """Get credit history summary for a company (for RAG context)"""
        cursor = self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_transactions,
                    SUM(inflow) as total_inflow,
                    SUM(outflow) as total_outflow,
                    SUM(inflow) - SUM(outflow) as net_position,
                    currency,
                    MIN(transaction_date) as earliest_transaction,
                    MAX(transaction_date) as latest_transaction,
                    COUNT(DISTINCT bank) as banks_count
                FROM credit_history
                WHERE shopify_company_id = %s
                GROUP BY currency
            """, (shopify_company_id,))
            
            summaries = cursor.fetchall()
            
            return {
                "shopify_company_id": shopify_company_id,
                "currency_summaries": [dict(row) for row in summaries],
                "generated_at": datetime.now().isoformat()
            }
            
        finally:
            cursor.close()
