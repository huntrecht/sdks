"""Credit Risk resource — v1."""

from huntrecht.base import APIResource


class CreditAPI(APIResource):
    """Credit risk assessment and scoring."""

    def assess(
        self, customer_email: str, include_recommendations: bool = False
    ) -> dict:
        """Perform a credit risk assessment."""
        return self._request(
            "POST",
            "/credit/assess",
            json={
                "customer_email": customer_email,
                "include_recommendations": include_recommendations,
            },
        )

    def score(self, customer_email: str) -> dict:
        """Get the latest credit score for a customer."""
        return self._request("GET", f"/credit/score/{customer_email}")
