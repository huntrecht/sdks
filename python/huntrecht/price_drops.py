"""Price Drops resource — v1. Public endpoints (no auth required)."""

from huntrecht.base import APIResource


class PriceDropsAPI(APIResource):
    """Price drop events — public endpoints."""

    def list(self, limit: int = 10, min_discount: float = 5.0, days: int = 7) -> dict:
        """List recent price drops (public)."""
        if limit > 50:
            limit = 50
        return self._request(
            "GET",
            "/price-drops",
            params={
                "limit": limit,
                "min_discount": min_discount,
                "days": days,
            },
            auth_required=False,
        )

    def featured(self, limit: int = 10) -> dict:
        """Featured price drops for newsletters (public)."""
        if limit > 10:
            limit = 10
        return self._request(
            "GET",
            "/price-drops/featured",
            params={
                "limit": limit,
            },
            auth_required=False,
        )
