"""Orders resource — v1."""

from huntrecht.base import APIResource
from huntrecht.types_ import OrderListResponse


class OrdersAPI(APIResource):
    """Trade order management."""

    def list(
        self, page: int = 1, per_page: int = 20, status: str | None = None
    ) -> dict:
        """List paginated trade orders."""
        params: dict = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
        return self._request("GET", "/orders", params=params)

    def get(self, order_id: str) -> dict:
        """Get a single order by ID."""
        return self._request("GET", f"/orders/{order_id}")

    def create(
        self,
        commodity: str,
        quantity: float,
        delivery_terms: str = "FOB",
        destination: str | None = None,
        currency: str = "USD",
    ) -> dict:
        """Create a new trade order."""
        params: dict = {
            "commodity": commodity,
            "quantity": quantity,
            "delivery_terms": delivery_terms,
            "currency": currency,
        }
        if destination:
            params["destination"] = destination
        return self._request("POST", "/orders", params=params)
