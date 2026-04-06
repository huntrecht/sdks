"""Subscriptions resource — v1."""

from huntrecht.base import APIResource


class SubscriptionsAPI(APIResource):
    """B2B subscription management."""

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
        include_payment_history: bool = False,
    ) -> dict:
        """List paginated B2B subscriptions."""
        params: dict = {
            "page": page,
            "per_page": per_page,
            "include_payment_history": include_payment_history,
        }
        if status:
            params["status"] = status
        return self._request("GET", "/subscriptions", params=params)

    def get(self, subscription_id: str) -> dict:
        """Get a subscription with full details."""
        return self._request("GET", f"/subscriptions/{subscription_id}")
