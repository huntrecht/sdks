"""Arena resource — v1 execution/mutations (auth required)."""

from typing import Any

from huntrecht.base import APIResource


class ArenaAPI(APIResource):
    """TradeArena execution: orders, settlement, agents, risk, bonds."""

    def create_order(self, body: dict[str, Any]) -> dict:
        """Create an arena order."""
        return self._request("POST", "/arena/orders", json=body)

    def commit(self, order_id: str, body: dict[str, Any]) -> dict:
        """Commit to an arena order."""
        return self._request(
            "POST", f"/arena/orders/{order_id}/commit", json=body)

    def settle(self, order_id: str, settlement_price: float) -> dict:
        """Trigger settlement for an order."""
        return self._request(
            "POST", f"/arena/orders/{order_id}/settle",
            json={"settlement_price": settlement_price})

    def execute(self, order_id: str, body: dict[str, Any]) -> dict:
        """Execute a settled order via the swap executor."""
        return self._request(
            "POST", f"/arena/orders/{order_id}/execute", json=body)

    def generate(self, body: dict[str, Any]) -> dict:
        """Generate one order with oracle pricing."""
        return self._request("POST", "/arena/agent/generate", json=body)

    def generate_batch(self) -> dict:
        """Generate a batch of orders across asset types."""
        return self._request("POST", "/arena/agent/generate-batch")

    def market_signal(self, body: dict[str, Any]) -> dict:
        """Create an order from a market signal."""
        return self._request("POST", "/arena/agent/market-signal", json=body)

    def analyze_only(self, body: dict[str, Any]) -> dict:
        """Analyze a signal without creating an order."""
        return self._request("POST", "/arena/agent/analyze-only", json=body)

    def insurance_claim(self, order_id: str, commitment_id: str,
                        claim_type: str, claimed_amount: float,
                        evidence: dict[str, Any]) -> dict:
        """Submit an insurance claim."""
        return self._request(
            "POST", "/arena/risk/insurance/claim",
            params={"order_id": order_id, "commitment_id": commitment_id,
                    "claim_type": claim_type,
                    "claimed_amount": claimed_amount},
            json={"evidence": evidence})

    def bond_yield_order(self, bond_id: str, month: int) -> dict:
        """Create a monthly bond yield order."""
        return self._request(
            "POST", f"/arena/bonds/{bond_id}/yield-order",
            json={"month": month})

    def release_breaker(self, halt_id: str) -> dict:
        """Release a circuit breaker (staff)."""
        return self._request(
            "POST", "/arena/risk/circuit-breaker/release",
            params={"halt_id": halt_id})

    def reconcile(self, limit: int = 25, dry_run: bool = True) -> dict:
        """Run the validation reconciler (staff)."""
        return self._request(
            "POST", "/arena/validation/reconcile",
            params={"limit": limit, "dry_run": dry_run})
