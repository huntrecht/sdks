"""
Huntrecht Platform API Client — v1

Core HTTP client with automatic token management, retry logic,
rate-limit handling, and typed resource access.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any

import httpx

from huntrecht.exceptions import (
    HuntrechtError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    PermissionError,
)

logger = logging.getLogger(__name__)

API_VERSION = "v1"
DEFAULT_BASE_URL = "https://api.huntrecht.com"


class HuntrechtClient:
    """Client for the Huntrecht Platform API v1.

    Args:
        base_url: API base URL. Defaults to HUNTRECHT_BASE_URL env var or https://api.huntrecht.com
        client_id: OAuth2 client ID. Defaults to HUNTRECHT_CLIENT_ID env var.
        client_secret: OAuth2 client secret. Defaults to HUNTRECHT_CLIENT_SECRET env var.
        access_token: Pre-existing access token (skip auth if provided).
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts on 5xx/429 errors.
        retry_backoff: Base backoff in seconds for retries.

    Usage:
        client = HuntrechtClient(
            client_id="hnt_abc123",
            client_secret="secret"
        )
        client.auth.token()  # authenticate
        orders = client.orders.list()
    """

    def __init__(
        self,
        base_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        access_token: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
    ):
        self.base_url = (
            base_url or os.getenv("HUNTRECHT_BASE_URL", DEFAULT_BASE_URL)
        ).rstrip("/")
        self.client_id = client_id or os.getenv("HUNTRECHT_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("HUNTRECHT_CLIENT_SECRET", "")
        self._access_token = access_token
        self._refresh_token: str | None = None
        self._token_expires_at: float = 0
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self._http = httpx.Client(
            base_url=f"{self.base_url}/api/{API_VERSION}",
            timeout=self.timeout,
            headers={
                "User-Agent": f"huntrecht-sdk-python/{__import__('huntrecht').__version__}"
            },
        )

        # Resource accessors — lazy-loaded
        from huntrecht.auth import AuthAPI
        from huntrecht.clients import ClientsAPI
        from huntrecht.orders import OrdersAPI
        from huntrecht.payments import PaymentsAPI
        from huntrecht.subscriptions import SubscriptionsAPI
        from huntrecht.credit import CreditAPI
        from huntrecht.kyc import KycAPI
        from huntrecht.quotes import QuotesAPI
        from huntrecht.users import UsersAPI
        from huntrecht.storefront import StorefrontAPI
        from huntrecht.price_drops import PriceDropsAPI
        from huntrecht.app_proxy import AppProxyAPI
        from huntrecht.linked_payments import LinkedPaymentsAPI

        self.auth = AuthAPI(self)
        self.clients = ClientsAPI(self)
        self.orders = OrdersAPI(self)
        self.payments = PaymentsAPI(self)
        self.subscriptions = SubscriptionsAPI(self)
        self.credit = CreditAPI(self)
        self.kyc = KycAPI(self)
        self.quotes = QuotesAPI(self)
        self.users = UsersAPI(self)
        self.storefront = StorefrontAPI(self)
        self.price_drops = PriceDropsAPI(self)
        self.app_proxy = AppProxyAPI(self)
        self.linked_payments = LinkedPaymentsAPI(self)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth_required: bool = True,
    ) -> dict[str, Any]:
        """Make an API request with automatic auth, retry, and rate-limit handling.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (without /api/v1 prefix)
            params: Query parameters
            json: JSON body
            headers: Additional headers
            auth_required: Whether to include Bearer token

        Returns:
            Parsed JSON response

        Raises:
            AuthenticationError: If auth fails
            RateLimitError: If rate limited after all retries
            NotFoundError: If resource not found
            ValidationError: If request validation fails
            PermissionError: If insufficient permissions
            HuntrechtError: For other API errors
        """
        if auth_required:
            self._ensure_token()

        req_headers = {"Accept": "application/json"}
        if auth_required and self._access_token:
            req_headers["Authorization"] = f"Bearer {self._access_token}"
        if headers:
            req_headers.update(headers)

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self._http.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                    headers=req_headers,
                )
                return self._handle_response(response)

            except RateLimitError as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = (
                        e.retry_after
                        if e.retry_after > 0
                        else self.retry_backoff * (2**attempt)
                    )
                    logger.warning(
                        f"Rate limited. Retrying in {wait:.1f}s (attempt {attempt + 1})"
                    )
                    time.sleep(wait)
                    continue
                raise

            except httpx.HTTPError as e:
                last_error = HuntrechtError(f"HTTP error: {e}")
                if attempt < self.max_retries:
                    wait = self.retry_backoff * (2**attempt)
                    logger.warning(
                        f"HTTP error. Retrying in {wait:.1f}s (attempt {attempt + 1})"
                    )
                    time.sleep(wait)
                    continue
                raise HuntrechtError(
                    f"Request failed after {self.max_retries + 1} attempts: {e}"
                ) from e

        raise last_error or HuntrechtError("Request failed")

    def _ensure_token(self) -> None:
        """Ensure a valid access token exists, refreshing if needed."""
        if self._access_token and time.time() < self._token_expires_at:
            return

        if self.client_id and self.client_secret:
            from huntrecht.auth import AuthAPI

            auth = AuthAPI(self)
            try:
                tokens = auth.token()
                self._access_token = tokens["access_token"]
                self._refresh_token = tokens.get("refresh_token")
                self._token_expires_at = (
                    time.time() + tokens.get("expires_in", 1800) - 60
                )
            except AuthenticationError:
                raise
        else:
            raise AuthenticationError(
                "No access token and no client credentials. "
                "Set HUNTRECHT_CLIENT_ID and HUNTRECHT_CLIENT_SECRET, "
                "or pass them to HuntrechtClient()."
            )

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle HTTP response, raising appropriate exceptions."""
        if response.status_code == 204:
            return {}

        try:
            data = response.json()
        except Exception:
            data = {"raw": response.text}

        if response.status_code == 401:
            self._access_token = None
            raise AuthenticationError(
                data.get("error_description", "Authentication failed"),
                status_code=401,
                response=data,
            )

        if response.status_code == 403:
            raise PermissionError(
                data.get("error_description", "Insufficient permissions"),
                status_code=403,
                response=data,
            )

        if response.status_code == 404:
            raise NotFoundError(
                data.get("error_description", "Resource not found"),
                status_code=404,
                response=data,
            )

        if response.status_code == 422:
            raise ValidationError(
                data.get("error_description", "Validation failed"),
                status_code=422,
                response=data,
            )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                data.get("error_description", "Rate limit exceeded"),
                status_code=429,
                retry_after=retry_after,
                response=data,
            )

        if response.status_code >= 400:
            raise HuntrechtError(
                data.get("error_description", f"HTTP {response.status_code}"),
                status_code=response.status_code,
                response=data,
            )

        return data

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> HuntrechtClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
