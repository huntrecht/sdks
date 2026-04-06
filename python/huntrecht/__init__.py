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
    HuntrechtError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    PermissionError,
)
from huntrecht.types_ import (
    TokenResponse,
    ApiClientResponse,
    ApiClientWithSecret,
    UserProfile,
    Order,
    OrderListResponse,
    Payment,
    PaymentListResponse,
    Subscription,
    SubscriptionListResponse,
    CreditScoreData,
    CreditAssessmentData,
    KycSubmission,
    KycListResponse,
    CommodityQuote,
    QuoteListResponse,
    CollectionResponse,
    ProductResponse,
    PriceDropEvent,
    PriceDropListResponse,
    PaymentEligibilityResponse,
    LinkedWallet,
    LinkedBank,
    LinkedAccountsResponse,
)

__version__ = "0.1.0"
__all__ = [
    "HuntrechtClient",
    "HuntrechtError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "PermissionError",
    "TokenResponse",
    "ApiClientResponse",
    "ApiClientWithSecret",
    "UserProfile",
    "Order",
    "OrderListResponse",
    "Payment",
    "PaymentListResponse",
    "Subscription",
    "SubscriptionListResponse",
    "CreditScoreData",
    "CreditAssessmentData",
    "KycSubmission",
    "KycListResponse",
    "CommodityQuote",
    "QuoteListResponse",
    "CollectionResponse",
    "ProductResponse",
    "PriceDropEvent",
    "PriceDropListResponse",
    "PaymentEligibilityResponse",
    "LinkedWallet",
    "LinkedBank",
    "LinkedAccountsResponse",
]
