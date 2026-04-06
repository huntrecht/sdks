"""
Strawberry GraphQL Schema for Credit History Data Connect Server
"""
import strawberry
from typing import List, Optional
from datetime import datetime
from sdk.python.credit_history_types import (
    CreditTransaction,
    CreditHistoryConnection,
    CreditHistoryEdge,
    PageInfo,
    CreditHistoryInput,
    IngestResult
)


@strawberry.type
class Query:
    """GraphQL queries for credit history data"""
    
    @strawberry.field
    def credit_history(
        self,
        company_id: str,
        shopify_company_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
        info: strawberry.Info = None
    ) -> CreditHistoryConnection:
        """
        Fetch credit history for a company with pagination
        """
        from sdk.python.credit_history_resolvers import CreditHistoryResolver
        from oauth_auth import get_db_connection
        
        db = get_db_connection()
        try:
            resolver = CreditHistoryResolver(db_connection=db)
            return resolver.get_credit_history(
                company_id=company_id,
                shopify_company_id=shopify_company_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                cursor=cursor
            )
        finally:
            db.close()
    
    @strawberry.field
    def company_credit_summary(
        self,
        shopify_company_id: str,
        info: strawberry.Info = None
    ) -> strawberry.scalars.JSON:
        """
        Get aggregated credit history summary for a Shopify B2B company
        """
        from sdk.python.credit_history_resolvers import CreditHistoryResolver
        from oauth_auth import get_db_connection
        
        db = get_db_connection()
        try:
            resolver = CreditHistoryResolver(db_connection=db)
            return resolver.get_company_summary(shopify_company_id)
        finally:
            db.close()


@strawberry.type
class Mutation:
    """GraphQL mutations for credit history data ingestion"""
    
    @strawberry.mutation
    async def ingest_credit_history(
        self,
        provider_id: str,
        company_id: str,
        records: List[CreditHistoryInput],
        enrich_shopify: bool = True,
        info: strawberry.Info = None
    ) -> IngestResult:
        """
        Ingest credit history records from a data provider
        
        Args:
            provider_id: Data provider identifier
            company_id: External company ID
            records: List of credit history records
            enrich_shopify: Whether to map/create Shopify B2B companies
        """
        from sdk.python.credit_history_resolvers import CreditHistoryResolver
        from oauth_auth import get_db_connection
        
        db = get_db_connection()
        try:
            resolver = CreditHistoryResolver(db_connection=db)
            return await resolver.ingest_records(
                provider_id=provider_id,
                company_id=company_id,
                records=records,
                enrich_shopify=enrich_shopify
            )
        finally:
            db.close()
    
    @strawberry.mutation
    async def trigger_provider_sync(
        self,
        provider_id: str,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        info: strawberry.Info = None
    ) -> IngestResult:
        """
        Trigger automatic sync from a registered data provider
        
        Args:
            provider_id: Registered data provider ID
            company_id: External company ID to sync
            start_date: Optional start date for sync
            end_date: Optional end date for sync
        """
        from sdk.python.credit_history_resolvers import CreditHistoryResolver
        from oauth_auth import get_db_connection
        
        db = get_db_connection()
        try:
            resolver = CreditHistoryResolver(db_connection=db)
            return await resolver.trigger_sync(
                provider_id=provider_id,
                company_id=company_id,
                start_date=start_date,
                end_date=end_date
            )
        finally:
            db.close()


# Create the GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
