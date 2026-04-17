import logging

from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
from supabase import create_client, Client

from app.config import settings

logger = logging.getLogger(__name__)


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
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as e:
        logger.error("JWT verification failed: %s", e)
        # Try without audience check in case aud claim differs
        try:
            payload_debug = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            logger.error("Token decoded without aud check. aud=%s, iss=%s", payload_debug.get("aud"), payload_debug.get("iss"))
        except JWTError as e2:
            logger.error("Token also failed without aud check: %s", e2)
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}")

    # Email whitelist check
    email = payload.get("email", "")
    allowed = [e.strip() for e in settings.ALLOWED_EMAILS.split(",") if e.strip()]
    if email not in allowed:
        raise HTTPException(status_code=403, detail="Access denied: email not in allowed list")

    return payload
