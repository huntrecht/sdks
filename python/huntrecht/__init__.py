"""
Huntrecht Platform SDK for Python

Official Python client for the Huntrecht Platform API v1.
Provides typed access to authentication, orders, subscriptions,
credit risk, KYC, quotes, storefront, and payments.

Usage:
    from huntrecht import HuntrechtClient

    client = HuntrechtClient(
        base_url="https://api.huntrecht.com",
        client_id="hnt_your_client_id",
        client_secret="your_secret"
    )

    # Authenticate
    tokens = client.auth.token()
    print(f"Access token expires in {tokens.expires_in}s")

    # List orders
    orders = client.orders.list()
    for order in orders.data:
        print(f"Order {order.id}: {order.commodity}")
"""

from huntrecht.client import HuntrechtClient
from huntrecht.exceptions import (
    AuthenticationError,
    HuntrechtError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ValidationError,
)
from huntrecht.types_ import (
    ApiClientResponse,
    ApiClientWithSecret,
    CollectionResponse,
    CommodityQuote,
    CreditAssessmentData,
    CreditScoreData,
    KycListResponse,
    KycSubmission,
    LinkedAccountsResponse,
    LinkedBank,
    LinkedWallet,
    Order,
    OrderListResponse,
    Payment,
    PaymentEligibilityResponse,
    PaymentListResponse,
    PriceDropEvent,
    PriceDropListResponse,
    ProductResponse,
    QuoteListResponse,
    Subscription,
    SubscriptionListResponse,
    TokenResponse,
    UserProfile,
)

__version__ = "0.3.0"
__all__ = [
    "ApiClientResponse",
    "ApiClientWithSecret",
    "AuthenticationError",
    "CollectionResponse",
    "CommodityQuote",
    "CreditAssessmentData",
    "CreditScoreData",
    "HuntrechtClient",
    "HuntrechtError",
    "KycListResponse",
    "KycSubmission",
    "LinkedAccountsResponse",
    "LinkedBank",
    "LinkedWallet",
    "NotFoundError",
    "Order",
    "OrderListResponse",
    "Payment",
    "PaymentEligibilityResponse",
    "PaymentListResponse",
    "PermissionError",
    "PriceDropEvent",
    "PriceDropListResponse",
    "ProductResponse",
    "QuoteListResponse",
    "RateLimitError",
    "Subscription",
    "SubscriptionListResponse",
    "TokenResponse",
    "UserProfile",
    "ValidationError",
]
