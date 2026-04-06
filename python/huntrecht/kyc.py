"""KYC resource — v1."""

from huntrecht.base import APIResource


class KycAPI(APIResource):
    """KYC submission management."""

    def list(
        self, page: int = 1, per_page: int = 20, status: str | None = None
    ) -> dict:
        """List KYC submissions (paginated)."""
        params: dict = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
        return self._request("GET", "/kyc", params=params)

    def get(self, submission_id: str) -> dict:
        """Get a single KYC submission."""
        return self._request("GET", f"/kyc/{submission_id}")

    def submit(
        self,
        company_name: str,
        company_type: str,
        registration_number: str | None = None,
        address: dict[str, str] | None = None,
        contact_info: dict[str, str] | None = None,
    ) -> dict:
        """Submit KYC/onboarding info."""
        body: dict = {"company_name": company_name, "company_type": company_type}
        if registration_number is not None:
            body["registration_number"] = registration_number
        if address is not None:
            body["address"] = address
        if contact_info is not None:
            body["contact_info"] = contact_info
        return self._request("POST", "/kyc", json=body)
