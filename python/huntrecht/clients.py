"""API Clients resource — v1."""

from __future__ import annotations

from huntrecht.base import APIResource


class ClientsAPI(APIResource):
    """Manage API clients (OAuth2 credentials)."""

    def list(self, user_id: int) -> dict:
        """List all API clients for a user."""
        return self._request("GET", "/clients", params={"user_id": user_id})

    def create(
        self,
        user_id: int,
        client_name: str,
        description: str | None = None,
        webhook_url: str | None = None,
        ip_allowlist: list[str] | None = None,
        scopes: list[str] | None = None,
    ) -> dict:
        """Create a new API client. Returns secret only once."""
        body: dict = {"client_name": client_name}
        if description is not None:
            body["description"] = description
        if webhook_url is not None:
            body["webhook_url"] = webhook_url
        if ip_allowlist is not None:
            body["ip_allowlist"] = ip_allowlist
        if scopes is not None:
            body["scopes"] = scopes
        return self._request("POST", "/clients", params={"user_id": user_id}, json=body)

    def update(self, user_id: int, client_id: str, **kwargs) -> dict:
        """Update an API client."""
        return self._request(
            "PATCH", f"/clients/{client_id}", params={"user_id": user_id}, json=kwargs
        )

    def rotate_secret(self, user_id: int, client_id: str) -> dict:
        """Rotate an API client's secret."""
        return self._request("POST", f"/clients/{client_id}/rotate", params={"user_id": user_id})

    def delete(self, user_id: int, client_id: str) -> dict:
        """Delete an API client."""
        return self._request("DELETE", f"/clients/{client_id}", params={"user_id": user_id})
