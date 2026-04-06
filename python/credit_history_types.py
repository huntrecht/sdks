"""
Pydantic models and Strawberry GraphQL types for credit history data
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field
import strawberry


class CreditHistoryRecord(BaseModel):
    """Pydantic model for credit history record with validation"""
    company_id: str = Field(..., description="External company identifier from provider")
    email: EmailStr = Field(..., description="Company contact email")
    date: datetime = Field(..., description="Transaction date")
    reference: str = Field(..., description="Transaction reference/description")
    
    inflow: Optional[float] = Field(None, ge=0, description="Money received (credit)")
    outflow: Optional[float] = Field(None, ge=0, description="Money spent (debit)")
    balance: Optional[float] = Field(None, description="Running balance after transaction")
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    bank: Optional[str] = None
    currency: Optional[str] = Field(default="USD", description="ISO 4217 currency code")
    
    shopify_company_id: Optional[str] = Field(None, description="Mapped Shopify B2B company GID")
    provider_id: Optional[str] = Field(None, description="Data provider identifier")
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "ext_company_12345",
                "email": "finance@acmecorp.com",
                "date": "2025-01-15T10:30:00Z",
                "reference": "Invoice payment - INV-2025-001",
                "inflow": 50000.00,
                "outflow": 0.00,
                "balance": 125000.00,
                "account_name": "Acme Corporation Ltd",
                "account_number": "****1234",
                "bank": "First National Bank",
                "currency": "USD"
            }
        }


@strawberry.type
class CreditTransaction:
    """GraphQL type for credit transaction"""
    id: str
    company_id: str
    email: str
    date: datetime
    reference: str
    inflow: Optional[float] = None
    outflow: Optional[float] = None
    balance: Optional[float] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    bank: Optional[str] = None
    currency: Optional[str] = None
    shopify_company_id: Optional[str] = None
    provider_id: Optional[str] = None


@strawberry.type
class PageInfo:
    """Pagination info following Relay cursor spec"""
    has_next_page: bool
    end_cursor: Optional[str] = None


@strawberry.type
class CreditHistoryEdge:
    """Edge containing a credit transaction node and cursor"""
    node: CreditTransaction
    cursor: str


@strawberry.type
class CreditHistoryConnection:
    """Paginated connection for credit history"""
    edges: List[CreditHistoryEdge]
    page_info: PageInfo
    total_count: int


@strawberry.input
class CreditHistoryInput:
    """Input for creating/updating credit history records"""
    company_id: str
    email: str
    date: datetime
    reference: str
    inflow: Optional[float] = None
    outflow: Optional[float] = None
    balance: Optional[float] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    bank: Optional[str] = None
    currency: Optional[str] = "USD"
    provider_id: Optional[str] = None
    metadata: Optional[strawberry.scalars.JSON] = None


@strawberry.type
class IngestResult:
    """Result of credit history ingestion"""
    success: bool
    records_processed: int
    records_enriched: int
    shopify_companies_created: int
    errors: List[str]
