import logging

from fastapi import Depends, HTTPException, Header
from supabase import create_client, Client

from app.config import settings

logger = logging.getLogger(__name__)

# Shared Supabase client (service role)
_supabase: Client | None = None


def get_supabase_client() -> Client:
    """Get or create a Supabase client using the service role key (bypasses RLS)."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _supabase


async def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Verify Supabase JWT by calling Supabase auth.get_user().
    Returns user metadata dict with email, id, etc.
    Raises 401 if token is missing or invalid.
    Raises 403 if the user's email is not in the allowed list.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.removeprefix("Bearer ")

    try:
        sb = get_supabase_client()
        user_response = sb.auth.get_user(token)
        user = user_response.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error("Token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Email whitelist check
    email = user.email or ""
    allowed = [e.strip() for e in settings.ALLOWED_EMAILS.split(",") if e.strip()]
    if email not in allowed:
        raise HTTPException(status_code=403, detail="Access denied: email not in allowed list")

    return {"sub": user.id, "email": user.email}
