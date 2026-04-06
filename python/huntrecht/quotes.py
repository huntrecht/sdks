"""Quotes resource — v1."""

from huntrecht.base import APIResource


class QuotesAPI(APIResource):
    """Commodity quote management."""

    def list(self, page: int = 1, per_page: int = 20) -> dict:
        """List commodity quotes (paginated)."""
        return self._request(
            "GET", "/quotes", params={"page": page, "per_page": per_page}
        )

    def get(self, quote_id: str) -> dict:
        """Get a single quote by ID."""
        return self._request("GET", f"/quotes/{quote_id}")

    def create(
        self,
        commodity: str,
        quantity: float,
        unit: str = "kg",
        delivery_location: str | None = None,
    ) -> dict:
        """Request a new commodity quote."""
        body: dict = {"commodity": commodity, "quantity": quantity, "unit": unit}
        if delivery_location is not None:
            body["delivery_location"] = delivery_location
        return self._request("POST", "/quotes", json=body)
