"""GreenCloud resource — v1. Public pricing feed + estimate calculator."""

from huntrecht.base import APIResource

CALCULATOR_TERMS = (3, 6, 12, 24, 36)


class GreenCloudAPI(APIResource):
    """Published GreenCloud catalog pricing and estimates (no auth)."""

    def pricing(self) -> dict:
        """Public pricing feed (cacheable)."""
        return self._request(
            "GET",
            "/greencloud/pricing",
            auth_required=False,
        )

    def calculate_estimate(self, sku: str, nodes: int = 1,
                           term_months: int = 12) -> dict:
        """Server-calculated estimate (non-binding, not a capacity
        reservation)."""
        if term_months not in CALCULATOR_TERMS:
            raise ValueError(
                f"term_months must be one of {CALCULATOR_TERMS}")
        if not isinstance(nodes, int) or isinstance(nodes, bool) \
                or not 1 <= nodes <= 256:
            raise ValueError("nodes must be an integer 1..256")
        return self._request(
            "POST",
            "/greencloud/calculator",
            json={"sku": sku, "nodes": nodes, "term_months": term_months},
            auth_required=False,
        )
