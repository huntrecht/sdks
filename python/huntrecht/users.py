"""Users resource — v1."""

from huntrecht.base import APIResource


class UsersAPI(APIResource):
    """User profile operations."""

    def me(self) -> dict:
        """Get current authenticated user profile."""
        return self._request("GET", "/users/me")

    def get(self, user_id: str) -> dict:
        """Get user profile by ID (own profile only unless admin)."""
        return self._request("GET", f"/users/{user_id}")
