"""Payments resource — v1."""

from huntrecht.base import APIResource


class PaymentsAPI(APIResource):
    """Payment management."""

    def list(
        self, page: int = 1, per_page: int = 20, status: str | None = None
    ) -> dict:
        """List paginated payments."""
        params: dict = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
        return self._request("GET", "/payments", params=params)

    def get(self, payment_id: str) -> dict:
        """Get a single payment by ID."""
        return self._request("GET", f"/payments/{payment_id}")

    def create(
        self,
        subscription_id: int,
        amount: float,
        currency: str = "USD",
        payment_method: str = "card",
    ) -> dict:
        """Create a payment for a subscription."""
        return self._request(
            "POST",
            "/payments",
            json={
                "subscription_id": subscription_id,
                "amount": amount,
                "currency": currency,
                "payment_method": payment_method,
            },
        )
