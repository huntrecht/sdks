"""
Shopify B2B Company Registry Service
Maps external company IDs to Shopify B2B company GIDs
Auto-creates companies that don't exist
"""
import asyncio
from typing import Optional, Dict
from datetime import datetime, timedelta
import psycopg2.extras
from shopify_admin_client import ShopifyAdminClient


class ShopifyCompanyRegistry:
    """Service for mapping external company IDs to Shopify B2B companies"""
    
    def __init__(self, admin_client: ShopifyAdminClient, db_connection):
        self.admin_client = admin_client
        self.db_connection = db_connection
        self._cache: Dict[str, str] = {}
        self._cache_ttl = timedelta(hours=1)
        self._cache_timestamps: Dict[str, datetime] = {}
    
    async def get_or_create_company(
        self,
        external_company_id: str,
        email: str,
        company_name: Optional[str] = None,
        **contact_info
    ) -> str:
        """
        Get Shopify company GID for external company ID.
        Creates company if it doesn't exist.
        
        Args:
            external_company_id: External provider's company identifier
            email: Company contact email
            company_name: Company name (defaults to external_company_id)
            **contact_info: Additional contact details (first_name, last_name, phone, etc.)
        
        Returns:
            Shopify B2B company GID (e.g., gid://shopify/Company/12345)
        """
        # Check cache first
        cached_id = self._get_from_cache(external_company_id)
        if cached_id:
            return cached_id
        
        # Check database mapping
        db_company_id = self._get_from_db(external_company_id)
        if db_company_id:
            self._set_cache(external_company_id, db_company_id)
            return db_company_id
        
        # Search Shopify by email or external ID
        shopify_company_id = await self._search_shopify_company(external_company_id, email)
        
        if not shopify_company_id:
            # Company doesn't exist - create it
            shopify_company_id = await self._create_shopify_company(
                external_company_id,
                email,
                company_name or f"Company {external_company_id}",
                **contact_info
            )
        
        # Store mapping in database
        self._store_mapping(external_company_id, shopify_company_id)
        self._set_cache(external_company_id, shopify_company_id)
        
        return shopify_company_id
    
    async def _search_shopify_company(
        self,
        external_id: str,
        email: str
    ) -> Optional[str]:
        """Search for existing Shopify company by external ID or email"""
        query = """
        query SearchCompany($query: String!) {
          companies(first: 1, query: $query) {
            edges {
              node {
                id
                externalId
              }
            }
          }
        }
        """
        
        try:
            # Try searching by external ID first
            result = await self.admin_client._make_graphql_request(
                query,
                {"query": f"externalId:{external_id}"}
            )
            
            companies = result.get("data", {}).get("companies", {}).get("edges", [])
            if companies:
                return companies[0]["node"]["id"]
            
            # Try searching by email
            result = await self.admin_client._make_graphql_request(
                query,
                {"query": f"email:{email}"}
            )
            
            companies = result.get("data", {}).get("companies", {}).get("edges", [])
            if companies:
                return companies[0]["node"]["id"]
            
            return None
        except Exception as e:
            print(f"⚠️  Error searching Shopify company: {e}")
            return None
    
    async def _create_shopify_company(
        self,
        external_id: str,
        email: str,
        company_name: str,
        **contact_info
    ) -> str:
        """Create new Shopify B2B company"""
        print(f"🏢 Creating Shopify B2B company for {external_id} ({email})")
        
        # Extract contact details with defaults
        first_name = contact_info.get("first_name", "")
        last_name = contact_info.get("last_name", "")
        phone = contact_info.get("phone", "")
        address1 = contact_info.get("address1", "N/A")
        city = contact_info.get("city", "N/A")
        province = contact_info.get("province", "N/A")
        zip_code = contact_info.get("zip", "00000")
        country_code = contact_info.get("country_code", "US")
        
        try:
            result = await self.admin_client.create_company(
                company_name=company_name,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                address1=address1,
                city=city,
                province=province,
                zip_code=zip_code,
                country_code=country_code,
                tax_id=external_id  # Use external ID as tax ID for mapping
            )
            
            company_data = result.get("data", {}).get("companyCreate", {}).get("company")
            if not company_data:
                errors = result.get("data", {}).get("companyCreate", {}).get("userErrors", [])
                raise Exception(f"Failed to create company: {errors}")
            
            company_id = company_data["id"]
            print(f"✅ Created Shopify B2B company: {company_id}")
            return company_id
            
        except Exception as e:
            print(f"❌ Error creating Shopify company: {e}")
            raise
    
    def _get_from_cache(self, external_id: str) -> Optional[str]:
        """Get company ID from cache if not expired"""
        if external_id in self._cache:
            timestamp = self._cache_timestamps.get(external_id)
            if timestamp and datetime.now() - timestamp < self._cache_ttl:
                return self._cache[external_id]
            else:
                # Expired - remove from cache
                del self._cache[external_id]
                del self._cache_timestamps[external_id]
        return None
    
    def _set_cache(self, external_id: str, shopify_id: str):
        """Store company ID in cache"""
        self._cache[external_id] = shopify_id
        self._cache_timestamps[external_id] = datetime.now()
    
    def _get_from_db(self, external_id: str) -> Optional[str]:
        """Get company ID from database mapping"""
        cursor = self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("""
                SELECT shopify_company_id
                FROM company_id_mappings
                WHERE external_company_id = %s
            """, (external_id,))
            
            result = cursor.fetchone()
            return result["shopify_company_id"] if result else None
        finally:
            cursor.close()
    
    def _store_mapping(self, external_id: str, shopify_id: str):
        """Store company ID mapping in database"""
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO company_id_mappings (
                    external_company_id,
                    shopify_company_id,
                    created_at
                )
                VALUES (%s, %s, NOW())
                ON CONFLICT (external_company_id)
                DO UPDATE SET
                    shopify_company_id = EXCLUDED.shopify_company_id,
                    updated_at = NOW()
            """, (external_id, shopify_id))
            
            self.db_connection.commit()
            print(f"✅ Stored mapping: {external_id} → {shopify_id}")
        except Exception as e:
            self.db_connection.rollback()
            print(f"⚠️  Error storing mapping: {e}")
        finally:
            cursor.close()
