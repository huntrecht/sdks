"""Linked Payments resource — v1."""

from huntrecht.base import APIResource


class LinkedPaymentsAPI(APIResource):
    """Linked wallet and bank payment methods."""

    def check_eligibility(
        self, customer_id: str, product_price: float = 0, b2b_exclusive: bool = False
    ) -> dict:
        """Check payment method eligibility (public)."""
        return self._request(
            "GET",
            "/linked-payments/check-eligibility",
            params={
                "customer_id": customer_id,
                "product_price": product_price,
                "b2b_exclusive": b2b_exclusive,
            },
            auth_required=False,
        )

    def link_wallet(
        self,
        customer_id: str,
        wallet_address: str | None = None,
        wallet_provider: str | None = None,
    ) -> dict:
        """Link a crypto wallet for B2B payments."""
        body: dict = {"customer_id": customer_id}
        if wallet_address:
            body["wallet_address"] = wallet_address
        if wallet_provider:
            body["wallet_provider"] = wallet_provider
        return self._request("POST", "/linked-payments/link-wallet", json=body)

    def link_bank(
        self,
        customer_id: str,
        plaid_access_token: str | None = None,
        account_id: str | None = None,
    ) -> dict:
        """Link a bank account via Plaid."""
        body: dict = {"customer_id": customer_id}
        if plaid_access_token:
            body["plaid_access_token"] = plaid_access_token
        if account_id:
            body["account_id"] = account_id
        return self._request("POST", "/linked-payments/link-bank", json=body)

    def linked_accounts(self, customer_id: str) -> dict:
        """Get linked wallets and banks for a customer."""
        return self._request("GET", f"/linked-payments/linked-accounts/{customer_id}")
