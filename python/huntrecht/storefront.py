"""Storefront resource — v1. Proxies Shopify Storefront API."""

from huntrecht.base import APIResource


class StorefrontAPI(APIResource):
    """Shopify storefront: collections, products, search."""

    def collections(self, first: int = 20, include_products: bool = False) -> dict:
        """List product collections."""
        if first > 100:
            first = 100
        return self._request(
            "GET",
            "/storefront/collections",
            params={
                "first": first,
                "include_products": include_products,
            },
        )

    def collection(self, handle: str, products_first: int = 20) -> dict:
        """Get collection by handle with products."""
        if products_first > 250:
            products_first = 250
        return self._request(
            "GET",
            f"/storefront/collections/{handle}",
            params={
                "products_first": products_first,
            },
        )

    def products(
        self, first: int = 20, after: str | None = None, b2b_only: bool = False
    ) -> dict:
        """List products with cursor pagination."""
        if first > 100:
            first = 100
        params: dict = {"first": first, "b2b_only": b2b_only}
        if after:
            params["after"] = after
        return self._request("GET", "/storefront/products", params=params)

    def product(self, handle: str) -> dict:
        """Get product by handle."""
        return self._request("GET", f"/storefront/products/{handle}")

    def search(self, query: str, first: int = 10, b2b_only: bool = False) -> dict:
        """Search products via Shopify predictive search."""
        if first > 50:
            first = 50
        return self._request(
            "GET",
            "/storefront/search",
            params={
                "query": query,
                "first": first,
                "b2b_only": b2b_only,
            },
        )
