import base64
import json
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

    # Decode header to find algorithm
    try:
        header_b64 = token.split(".")[0]
        header_b64 += "=" * (-len(header_b64) % 4)  # pad
        header_json = json.loads(base64.urlsafe_b64decode(header_b64))
        logger.error("TOKEN HEADER: %s", header_json)
    except Exception as e:
        logger.error("Failed to decode token header: %s", e)

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256", "HS384", "HS512"],
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
