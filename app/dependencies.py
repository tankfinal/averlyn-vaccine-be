import logging
import time

import httpx
from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
from supabase import create_client, Client

from app.config import settings

logger = logging.getLogger(__name__)

# Cache JWKS keys
_jwks_cache: dict | None = None
_jwks_cache_time: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour


async def _get_jwks() -> dict:
    """Fetch and cache JWKS from Supabase."""
    global _jwks_cache, _jwks_cache_time
    if _jwks_cache and (time.time() - _jwks_cache_time) < JWKS_CACHE_TTL:
        return _jwks_cache

    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/jwks"
    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_cache_time = time.time()
        logger.info("Fetched JWKS from %s", jwks_url)
        return _jwks_cache


def get_supabase_client() -> Client:
    """Create a Supabase client using the service role key (bypasses RLS)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


async def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Extract and verify Supabase JWT from Authorization: Bearer <token>.
    Returns the decoded JWT payload.
    Raises 401 if token is missing, invalid, or expired.
    Raises 403 if the user's email is not in the allowed list.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.removeprefix("Bearer ")

    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        kid = header.get("kid")

        if alg.startswith("ES") or alg.startswith("RS"):
            # Asymmetric — verify with JWKS public key
            jwks = await _get_jwks()
            key = None
            for k in jwks.get("keys", []):
                if k.get("kid") == kid:
                    key = k
                    break
            if not key:
                raise JWTError(f"No matching key found for kid={kid}")
            payload = jwt.decode(
                token, key, algorithms=[alg], audience="authenticated"
            )
        else:
            # Symmetric (HS256) — verify with JWT secret
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
    except JWTError as e:
        logger.error("JWT verification failed: %s", e)
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}")

    # Email whitelist check
    email = payload.get("email", "")
    allowed = [e.strip() for e in settings.ALLOWED_EMAILS.split(",") if e.strip()]
    if email not in allowed:
        raise HTTPException(status_code=403, detail="Access denied: email not in allowed list")

    return payload
