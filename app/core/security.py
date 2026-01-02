"""
Security & Authentication

Handles Supabase Auth with Google OAuth support.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.supabase import verify_supabase_token, get_supabase_client
from app.core.exceptions import unauthorized_exception


# Bearer token security scheme
security = HTTPBearer(auto_error=False)


class CurrentUser:
    """Authenticated user model"""
    def __init__(
        self,
        id: str,
        email: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        self.id = id
        self.email = email
        self.name = name
        self.avatar_url = avatar_url
        self.provider = provider

    @classmethod
    def from_supabase(cls, user_data: dict) -> "CurrentUser":
        """Create CurrentUser from Supabase user data"""
        metadata = user_data.get("user_metadata", {})
        app_metadata = user_data.get("app_metadata", {})

        return cls(
            id=user_data.get("id"),
            email=user_data.get("email"),
            name=metadata.get("full_name") or metadata.get("name"),
            avatar_url=metadata.get("avatar_url") or metadata.get("picture"),
            provider=app_metadata.get("provider"),
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    """
    Get current authenticated user from Supabase token.

    This is a FastAPI dependency that extracts and validates the JWT token
    from the Authorization header.

    Raises:
        HTTPException 401: If token is missing or invalid
    """
    if not credentials:
        raise unauthorized_exception("Missing authentication token")

    token = credentials.credentials
    user_data = await verify_supabase_token(token)

    if not user_data:
        raise unauthorized_exception("Invalid or expired token")

    return CurrentUser.from_supabase(user_data)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[CurrentUser]:
    """
    Get current user if authenticated, None otherwise.

    Use this for endpoints that work both authenticated and anonymously.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_auth(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Dependency that requires authentication.

    Use as: user: CurrentUser = Depends(require_auth)
    """
    return user
