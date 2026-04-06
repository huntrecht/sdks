"""Credit Risk API resource."""

from huntrecht.base import APIResource


class CreditRiskAPI(APIResource):
    """Credit risk assessment and scoring operations."""

    def get_score(self, customer_id: str) -> dict:
        """Get credit score for a customer.

        Args:
            customer_id: The customer ID

        Returns:
            dict with score, risk_level, and assessment details
        """
        return self._request(
            "GET", "/credit-risk/score", params={"customer_id": customer_id}
        )

    def assess(self, data: dict) -> dict:
        """Request a credit assessment.

        Args:
            data: Assessment data including customer_id, amount, purpose

        Returns:
            dict with assessment results
        """
        return self._request("POST", "/credit-risk/assess", json=data)

    def get_history(self, customer_id: str, limit: int = 20) -> dict:
        """Get credit history for a customer.

        Args:
            customer_id: The customer ID
            limit: Number of history records

        Returns:
            dict with credit history records
        """
        return self._request(
            "GET",
            "/data-connect/credit-history",
            params={
                "customer_id": customer_id,
                "limit": limit,
            },
        )

    def get_assessment(self, user_id: str) -> dict:
        """Get credit assessment for a company.

        Args:
            user_id: The user/company ID

        Returns:
            dict with credit assessment details
        """
        return self._request(
            "GET", f"/company/credit-assessment", params={"user_id": user_id}
        )

    def request_assessment(self, data: dict) -> dict:
        """Request a new credit assessment.

        Args:
            data: Assessment request data

        Returns:
            dict with assessment request status
        """
        return self._request("POST", "/company/credit-assessment/request", json=data)

    def get_improvement_options(self) -> dict:
        """Get available credit improvement options.

        Returns:
            dict with available improvement options
        """
        return self._request("GET", "/credit-improvement/available-options")

    def connect_wallet(self, data: dict) -> dict:
        """Connect a wallet for credit improvement.

        Args:
            data: Wallet connection data

        Returns:
            dict with connection status
        """
        return self._request("POST", "/credit-improvement/connect-wallet", json=data)

    def apply_boosts(self, data: dict) -> dict:
        """Apply credit improvement boosts.

        Args:
            data: Boost application data

        Returns:
            dict with boost results
        """
        return self._request("POST", "/credit-improvement/apply-boosts", json=data)
