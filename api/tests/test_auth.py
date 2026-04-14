"""
Tests for auth/dependencies.py.

The real token-validation flow makes HTTP calls to Azure JWKS endpoints and
uses python-jose to decode RSA-signed JWTs.  We mock those external calls to
exercise the logic without real Azure credentials.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.auth.dependencies import _resolve_role, get_current_admin, get_current_user

# ---------------------------------------------------------------------------
# _resolve_role
# ---------------------------------------------------------------------------


class TestResolveRole:
    def test_admin_role_in_roles(self):
        assert _resolve_role({"roles": ["Admin"]}) == "Admin"

    def test_multiple_roles_includes_admin(self):
        assert _resolve_role({"roles": ["Viewer", "Admin"]}) == "Admin"

    def test_no_roles(self):
        assert _resolve_role({"roles": []}) == "Viewer"

    def test_missing_roles_key(self):
        assert _resolve_role({}) == "Viewer"

    def test_non_admin_roles_only(self):
        assert _resolve_role({"roles": ["Viewer", "Editor"]}) == "Viewer"


# ---------------------------------------------------------------------------
# get_current_admin
# ---------------------------------------------------------------------------


class TestGetCurrentAdmin:
    async def test_allows_admin_user(self):
        admin_user = {
            "oid": "oid",
            "name": "Admin",
            "email": "admin@example-ngo.org",
            "roles": ["Admin"],
            "role": "Admin",
        }
        result = await get_current_admin(user=admin_user)
        assert result == admin_user

    async def test_rejects_viewer(self):
        viewer = {
            "oid": "oid",
            "name": "Viewer",
            "email": "viewer@example-ngo.org",
            "roles": [],
            "role": "Viewer",
        }
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin(user=viewer)
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# _validate_token and get_current_user
# ---------------------------------------------------------------------------


class TestValidateToken:
    async def test_valid_token_returns_user(self):
        """
        Mock _get_signing_keys and jwt.decode so that a fake token
        passes validation and returns user claims.
        """
        fake_jwks = {"keys": [{"kid": "test-kid", "kty": "RSA"}]}
        fake_payload = {
            "oid": "user-oid-001",
            "name": "Test User",
            "preferred_username": "test@example-ngo.org",
            "roles": ["Admin"],
            "sub": "subject",
        }

        with (
            patch("app.auth.dependencies._get_signing_keys", new=AsyncMock(return_value=fake_jwks)),
            patch("app.auth.dependencies.jwt.get_unverified_header", return_value={"kid": "test-kid"}),
            patch("app.auth.dependencies.jwt.decode", return_value=fake_payload),
        ):
            from fastapi.security import HTTPAuthorizationCredentials

            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake.jwt.token")
            user = await get_current_user(credentials=creds)

        assert user["oid"] == "user-oid-001"
        assert user["name"] == "Test User"
        assert user["email"] == "test@example-ngo.org"
        assert user["role"] == "Admin"

    async def test_invalid_token_header_raises_401(self):
        """JWTError on get_unverified_header should raise 401."""
        from jose import JWTError

        fake_jwks = {"keys": [{"kid": "test-kid"}]}

        with (
            patch("app.auth.dependencies._get_signing_keys", new=AsyncMock(return_value=fake_jwks)),
            patch(
                "app.auth.dependencies.jwt.get_unverified_header",
                side_effect=JWTError("bad header"),
            ),
        ):
            from fastapi.security import HTTPAuthorizationCredentials

            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token")
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        assert "Invalid token header" in exc_info.value.detail

    async def test_no_matching_signing_key_raises_401(self):
        """Token KID not found in JWKS should raise 401."""
        fake_jwks = {"keys": [{"kid": "different-kid"}]}

        with (
            patch("app.auth.dependencies._get_signing_keys", new=AsyncMock(return_value=fake_jwks)),
            patch("app.auth.dependencies.jwt.get_unverified_header", return_value={"kid": "missing-kid"}),
        ):
            from fastapi.security import HTTPAuthorizationCredentials

            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token.no.key")
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        assert "Unable to find matching signing key" in exc_info.value.detail

    async def test_all_decode_combinations_fail_raises_401(self):
        """All audience/issuer combinations fail → 401."""
        from jose import JWTError

        fake_jwks = {"keys": [{"kid": "test-kid"}]}

        with (
            patch("app.auth.dependencies._get_signing_keys", new=AsyncMock(return_value=fake_jwks)),
            patch("app.auth.dependencies.jwt.get_unverified_header", return_value={"kid": "test-kid"}),
            patch("app.auth.dependencies.jwt.decode", side_effect=JWTError("expired")),
        ):
            from fastapi.security import HTTPAuthorizationCredentials

            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired.token")
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        assert "Token validation failed" in exc_info.value.detail


# ---------------------------------------------------------------------------
# _get_signing_keys caching
# ---------------------------------------------------------------------------


class TestGetSigningKeys:
    async def test_caches_response(self):
        """Second call within TTL should not fetch from network."""
        import app.auth.dependencies as auth_mod

        fake_jwks = {"keys": []}
        mock_response = MagicMock()
        mock_response.json.return_value = {"jwks_uri": "https://example.com/jwks"}
        mock_response.raise_for_status = MagicMock()

        mock_jwks_response = MagicMock()
        mock_jwks_response.json.return_value = fake_jwks
        mock_jwks_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=[mock_response, mock_jwks_response])

        # Clear cache
        auth_mod._jwks_cache = None
        auth_mod._jwks_cache_time = 0

        with patch("app.auth.dependencies.httpx.AsyncClient", return_value=mock_client):
            result1 = await auth_mod._get_signing_keys()
            result2 = await auth_mod._get_signing_keys()

        # Only one network call — second is served from cache
        assert mock_client.get.call_count == 2  # fetched oidc + jwks once
        assert result1 == fake_jwks
        assert result2 == fake_jwks
