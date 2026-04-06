"""Typed dataclasses matching Platform API v1 response schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenResponse:
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 1800
    refresh_token: str | None = None
    scope: str = ""


@dataclass
class ApiClientResponse:
    id: int = 0
    client_id: str = ""
    client_name: str = ""
    description: str | None = None
    status: str = ""
    scopes: list[str] = field(default_factory=list)
    ip_allowlist: list[str] = field(default_factory=list)
    webhook_url: str | None = None
    created_at: str = ""
    last_used_at: str | None = None


@dataclass
class ApiClientWithSecret:
    id: int = 0
    client_id: str = ""
    client_name: str = ""
    description: str | None = None
    status: str = ""
    scopes: list[str] = field(default_factory=list)
    ip_allowlist: list[str] = field(default_factory=list)
    webhook_url: str | None = None
    created_at: str = ""
    last_used_at: str | None = None
    client_secret: str = ""


@dataclass
class UserProfile:
    id: int = 0
    email: str = ""
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str = ""
    permissions: list[str] = field(default_factory=list)
    company_name: str | None = None
    subscription_plan: str = ""
    email_verified: bool = False
    created_at: str = ""


@dataclass
class Order:
    id: str = ""
    user_id: str = ""
    commodity: str = ""
    quantity: float = 0.0
    delivery_terms: str = ""
    destination: str | None = None
    currency: str = ""
    status: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class OrderAggregate:
    total_orders: int = 0
    pending: int = 0
    confirmed: int = 0
    fulfilled: int = 0
    cancelled: int = 0


@dataclass
class Pagination:
    page: int = 1
    per_page: int = 20
    total: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False


@dataclass
class CursorPagination:
    has_next: bool = False
    end_cursor: str = ""


@dataclass
class OrderListResponse:
    data: list[Order] = field(default_factory=list)
    pagination: Pagination | None = None
    aggregates: OrderAggregate | None = None


@dataclass
class Payment:
    id: str = ""
    user_id: str = ""
    subscription_id: int = 0
    amount: float = 0.0
    currency: str = ""
    payment_method: str = ""
    status: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class PaymentListResponse:
    data: list[Payment] = field(default_factory=list)
    pagination: Pagination | None = None


@dataclass
class PaymentHistoryItem:
    id: str = ""
    amount: float = 0.0
    status: str = ""
    paid_at: str = ""


@dataclass
class Subscription:
    id: str = ""
    user_id: str = ""
    plan: str = ""
    status: str = ""
    amount: float = 0.0
    currency: str = ""
    billing_cycle: str = ""
    start_date: str = ""
    end_date: str | None = None
    payment_history: list[PaymentHistoryItem] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class SubscriptionListResponse:
    data: list[Subscription] = field(default_factory=list)
    pagination: Pagination | None = None


@dataclass
class CreditScoreData:
    credit_score: int = 0
    risk_level: str = ""
    fico_equivalent: int | None = None


@dataclass
class CreditAssessmentData:
    credit_score: int = 0
    risk_level: str = ""
    factors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    assessed_at: str = ""


@dataclass
class KycSubmission:
    id: str = ""
    user_id: str = ""
    company_name: str = ""
    company_type: str = ""
    registration_number: str | None = None
    address: str | None = None
    contact_info: str | None = None
    status: str = ""
    submitted_at: str = ""
    reviewed_at: str | None = None


@dataclass
class KycListResponse:
    data: list[KycSubmission] = field(default_factory=list)
    pagination: Pagination | None = None


@dataclass
class CommodityQuote:
    id: str = ""
    user_id: str = ""
    commodity: str = ""
    quantity: float = 0.0
    unit: str = ""
    delivery_location: str | None = None
    price: float = 0.0
    currency: str = ""
    status: str = ""
    valid_until: str = ""
    created_at: str = ""


@dataclass
class QuoteListResponse:
    data: list[CommodityQuote] = field(default_factory=list)
    pagination: Pagination | None = None


@dataclass
class CollectionResponse:
    id: str = ""
    title: str = ""
    handle: str = ""
    description: str | None = None
    image_url: str | None = None
    image_alt: str | None = None


@dataclass
class ProductResponse:
    id: str = ""
    title: str = ""
    handle: str = ""
    description: str | None = None
    price: float = 0.0
    currency: str = ""
    image_url: str | None = None
    available: bool = True
    b2b_exclusive: bool = False
    compare_at_price: float | None = None


@dataclass
class PriceDropEvent:
    product_id: str = ""
    product_title: str = ""
    product_handle: str = ""
    old_price: float = 0.0
    new_price: float = 0.0
    currency: str = ""
    image_url: str | None = None
    vendor: str | None = None
    discount_percentage: float = 0.0


@dataclass
class PriceDropListResponse:
    data: list[PriceDropEvent] = field(default_factory=list)
    count: int = 0


@dataclass
class PaymentEligibilityResponse:
    eligible: bool = False
    has_customer_role: bool = False
    is_b2b_product: bool = False
    available_methods: list[str] = field(default_factory=list)
    message: str = ""


@dataclass
class LinkedWallet:
    id: str = ""
    customer_id: str = ""
    wallet_address: str = ""
    wallet_provider: str = ""
    created_at: str = ""


@dataclass
class LinkedBank:
    id: str = ""
    customer_id: str = ""
    bank_name: str = ""
    account_masked: str = ""
    created_at: str = ""


@dataclass
class LinkedAccountsResponse:
    wallets: list[LinkedWallet] = field(default_factory=list)
    banks: list[LinkedBank] = field(default_factory=list)
    has_linked_payments: bool = False


def _parse_pagination(raw: dict[str, Any] | None) -> Pagination | None:
    if not raw:
        return None
    return Pagination(
        page=raw.get("page", 1),
        per_page=raw.get("per_page", 20),
        total=raw.get("total", 0),
        total_pages=raw.get("total_pages", 0),
        has_next=raw.get("has_next", False),
        has_prev=raw.get("has_prev", False),
    )


def _parse_orders(raw: dict[str, Any]) -> OrderListResponse:
    items = raw.get("data", [])
    return OrderListResponse(
        data=[Order(**o) for o in items],
        pagination=_parse_pagination(raw.get("pagination")),
        aggregates=OrderAggregate(**raw["aggregates"]) if "aggregates" in raw else None,
    )


def _parse_payments(raw: dict[str, Any]) -> PaymentListResponse:
    items = raw.get("data", [])
    return PaymentListResponse(
        data=[Payment(**p) for p in items],
        pagination=_parse_pagination(raw.get("pagination")),
    )


def _parse_subscriptions(raw: dict[str, Any]) -> SubscriptionListResponse:
    items = raw.get("data", [])
    return SubscriptionListResponse(
        data=[Subscription(**s) for s in items],
        pagination=_parse_pagination(raw.get("pagination")),
    )


def _parse_kyc_list(raw: dict[str, Any]) -> KycListResponse:
    items = raw.get("data", [])
    return KycListResponse(
        data=[KycSubmission(**k) for k in items],
        pagination=_parse_pagination(raw.get("pagination")),
    )


def _parse_quotes(raw: dict[str, Any]) -> QuoteListResponse:
    items = raw.get("data", [])
    return QuoteListResponse(
        data=[CommodityQuote(**q) for q in items],
        pagination=_parse_pagination(raw.get("pagination")),
    )


def _parse_price_drops(raw: dict[str, Any]) -> PriceDropListResponse:
    items = raw.get("data", [])
    return PriceDropListResponse(
        data=[PriceDropEvent(**p) for p in items],
        count=raw.get("count", 0),
    )


def _parse_linked_accounts(raw: dict[str, Any]) -> LinkedAccountsResponse:
    return LinkedAccountsResponse(
        wallets=[LinkedWallet(**w) for w in raw.get("wallets", [])],
        banks=[LinkedBank(**b) for b in raw.get("banks", [])],
        has_linked_payments=raw.get("has_linked_payments", False),
    )
