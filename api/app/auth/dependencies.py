import time

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

security = HTTPBearer()

_jwks_cache: dict | None = None
_jwks_cache_time: float = 0
_JWKS_TTL = 3600


async def _get_signing_keys() -> dict:
    global _jwks_cache, _jwks_cache_time

    now = time.time()
    if _jwks_cache and (now - _jwks_cache_time) < _JWKS_TTL:
        return _jwks_cache

    oidc_url = (
        f"https://login.microsoftonline.com/" f"{settings.AZURE_TENANT_ID}/v2.0/" f".well-known/openid-configuration"
    )
    async with httpx.AsyncClient() as client:
        oidc_resp = await client.get(oidc_url)
        oidc_resp.raise_for_status()
        jwks_uri = oidc_resp.json()["jwks_uri"]

        jwks_resp = await client.get(jwks_uri)
        jwks_resp.raise_for_status()
        jwks = jwks_resp.json()

    _jwks_cache = jwks
    _jwks_cache_time = now
    return jwks


async def _validate_token(token: str) -> dict:
    jwks = await _get_signing_keys()

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )

    kid = unverified_header.get("kid")
    rsa_key = None
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            rsa_key = key
            break

    if not rsa_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find matching signing key",
        )

    # Try combinations of audience and issuer formats
    # v1 tokens: aud=api://clientid, iss=https://sts.windows.net/{tenant}/
    # v2 tokens: aud=clientid, iss=https://login.microsoftonline.com/{tenant}/v2.0
    api_uri = f"api://{settings.AZURE_CLIENT_ID}"
    tid = settings.AZURE_TENANT_ID
    audiences = [settings.AZURE_CLIENT_ID, api_uri]
    issuers = [
        f"https://login.microsoftonline.com/{tid}/v2.0",
        f"https://sts.windows.net/{tid}/",
    ]

    token_payload = None
    last_error = None

    for aud in audiences:
        for iss in issuers:
            try:
                token_payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=aud,
                    issuer=iss,
                )
                break
            except JWTError as e:
                last_error = e
                continue
        if token_payload:
            break

    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(last_error)}",
        )

    return token_payload


def _resolve_role(payload: dict) -> str:
    """Determine user role from JWT claims. 'Admin' app role -> Admin, else Viewer."""
    roles = payload.get("roles", [])
    if "Admin" in roles:
        return "Admin"
    return "Viewer"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    payload = await _validate_token(credentials.credentials)
    return {
        "oid": payload.get("oid", ""),
        "name": payload.get("name", ""),
        "email": payload.get("preferred_username", ""),
        "roles": payload.get("roles", []),
        "role": _resolve_role(payload),
    }


async def get_current_admin(
    user: dict = Depends(get_current_user),
) -> dict:
    if user["role"] != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
