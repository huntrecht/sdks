"""Auth API resource — v1."""

from huntrecht.base import APIResource
from huntrecht.types_ import TokenResponse


class AuthAPI(APIResource):
    """Authentication: token, refresh, revoke."""

    def token(
        self,
        grant_type: str = "client_credentials",
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        scope: str | None = None,
    ) -> dict:
        """Obtain an access token.

        For ``client_credentials``: provide client_id + client_secret.
        For ``refresh_token``: provide refresh_token.
        """
        body: dict = {"grant_type": grant_type}
        if grant_type == "client_credentials":
            body["client_id"] = client_id or self._client.client_id
            body["client_secret"] = client_secret or self._client.client_secret
            if scope:
                body["scope"] = scope
        elif grant_type == "refresh_token":
            body["refresh_token"] = refresh_token or self._client._refresh_token or ""

        data = self._request("POST", "/auth/token", json=body, auth_required=False)
        self._client._access_token = data["access_token"]
        self._client._refresh_token = data.get("refresh_token")
        return data

    def revoke(self, token: str | None = None) -> dict:
        """Revoke an access or refresh token."""
        tok = token or self._client._access_token or ""
        return self._request(
            "POST", "/auth/revoke", params={"token": tok}, auth_required=False
        )
