"""
Supabase Client

Provides both public (anon) and admin (service role) clients.
"""

from typing import Optional

from supabase import create_client, Client

from app.config import settings


# Module-level clients (created once)
_anon_client: Optional[Client] = None
_admin_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get Supabase client with anon key (for user-context operations).

    This client respects Row Level Security (RLS) policies.
    """
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
        )
    return _anon_client


def get_supabase_admin_client() -> Client:
    """
    Get Supabase client with service role key (for admin operations).

    This client bypasses RLS - use with caution.
    """
    global _admin_client
    if _admin_client is None:
        _admin_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _admin_client


async def verify_supabase_token(access_token: str) -> Optional[dict]:
    """
    Verify a Supabase JWT token and return user info.

    Args:
        access_token: JWT access token from Supabase Auth

    Returns:
        User info dict if valid, None otherwise
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        client = get_supabase_client()
        logger.info(f"Verifying token (first 20 chars): {access_token[:20]}...")
        # Get user from token
        response = client.auth.get_user(access_token)
        logger.info(f"Auth response: {response}")
        if response and response.user:
            logger.info(f"User found: {response.user.email}")
            return {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata,
                "app_metadata": response.user.app_metadata,
            }
        logger.warning("No user in response")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


# Dependency for FastAPI
async def get_db() -> Client:
    """FastAPI dependency to get Supabase client."""
    return get_supabase_client()


async def get_admin_db() -> Client:
    """FastAPI dependency to get Supabase admin client."""
    return get_supabase_admin_client()
