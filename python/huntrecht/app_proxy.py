"""App Proxy resource — v1. Shopify theme proxy endpoints."""

from huntrecht.base import APIResource


class AppProxyAPI(APIResource):
    """Shopify App Proxy — returns Liquid-compatible responses."""

    def collections(self, first: int = 20, signature: str | None = None) -> dict:
        """Get collections for Shopify theme."""
        if first > 100:
            first = 100
        params: dict = {"first": first}
        if signature:
            params["signature"] = signature
        return self._request(
            "GET", "/app-proxy/collections", params=params, auth_required=False
        )

    def collection(
        self, handle: str, first: int = 20, signature: str | None = None
    ) -> dict:
        """Get collection with products for theme."""
        if first > 250:
            first = 250
        params: dict = {"first": first}
        if signature:
            params["signature"] = signature
        return self._request(
            "GET",
            f"/app-proxy/collections/{handle}",
            params=params,
            auth_required=False,
        )

    def price_drops(self, limit: int = 10, min_discount: float = 5.0) -> dict:
        """Get price drops for theme display (public)."""
        if limit > 20:
            limit = 20
        return self._request(
            "GET",
            "/app-proxy/price-drops",
            params={
                "limit": limit,
                "min_discount": min_discount,
            },
            auth_required=False,
        )

    def payment_methods(
        self,
        customer_id: str | None = None,
        product_price: float = 0,
        b2b_exclusive: bool = False,
        signature: str | None = None,
    ) -> dict:
        """Get available payment methods for theme."""
        params: dict = {"product_price": product_price, "b2b_exclusive": b2b_exclusive}
        if customer_id:
            params["customer_id"] = customer_id
        if signature:
            params["signature"] = signature
        return self._request(
            "GET", "/app-proxy/payment-methods", params=params, auth_required=False
        )
