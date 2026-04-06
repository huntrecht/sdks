"""Base API resource class for Huntrecht SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from huntrecht.client import HuntrechtClient


class APIResource:
    """Base class for all API resources."""

    def __init__(self, client: HuntrechtClient):
        self._client = client

    def _request(self, method: str, path: str, **kwargs):
        """Make an API request."""
        return self._client.request(method, path, **kwargs)
