"""
Auth API Endpoints

Authentication-related endpoints.
"""

from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user
from app.api.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get current authenticated user information.

    Requires a valid Supabase JWT token in the Authorization header.
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        provider=user.provider,
    )
