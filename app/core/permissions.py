"""
Permission Checking Utilities

Handles conversation access control for shared conversations.
"""

from enum import IntEnum
from typing import Optional, Tuple
from fastapi import HTTPException, status

from app.core.security import CurrentUser
from app.db.models.sharing import get_share_service
from app.db import get_conversation_service


class Permission(IntEnum):
    """Permission levels for conversation access."""
    NONE = 0
    VIEW = 1
    COMMENT = 2
    EDIT = 3
    OWNER = 4


PERMISSION_MAP = {
    "view": Permission.VIEW,
    "comment": Permission.COMMENT,
    "edit": Permission.EDIT,
    "owner": Permission.OWNER,
}


async def check_conversation_access(
    conversation_id: str,
    user: CurrentUser,
    required: Permission = Permission.VIEW,
) -> Tuple[dict, Permission]:
    """
    Check if user has required permission level for a conversation.

    Args:
        conversation_id: The conversation ID to check
        user: The current authenticated user
        required: Minimum required permission level

    Returns:
        Tuple of (conversation_data, user_permission_level)

    Raises:
        HTTPException 404: If conversation not found or no access
        HTTPException 403: If insufficient permissions
    """
    conversation_service = get_conversation_service()
    share_service = get_share_service()

    # First check if user is the owner
    conversation = await conversation_service.get_conversation(
        conversation_id, user.id
    )

    if conversation:
        return conversation, Permission.OWNER

    # Not owner, check shares
    permission_str = await share_service.get_user_permission(
        conversation_id, user.id
    )

    if not permission_str:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    permission = PERMISSION_MAP.get(permission_str, Permission.NONE)

    if permission < required:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {required.name.lower()}",
        )

    # Get conversation data using admin client (bypass RLS)
    from app.db.supabase import get_supabase_admin_client
    client = get_supabase_admin_client()
    result = client.table("conversations").select("*").eq("id", conversation_id).maybe_single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return result.data, permission


async def get_conversation_with_permission(
    conversation_id: str,
    user: CurrentUser,
) -> Tuple[dict, Permission]:
    """
    Get conversation and user's permission level.

    Similar to check_conversation_access but doesn't require a minimum permission.
    Returns (conversation, permission) or (None, NONE) if no access.
    """
    try:
        return await check_conversation_access(
            conversation_id, user, Permission.VIEW
        )
    except HTTPException:
        return None, Permission.NONE


async def require_owner(
    conversation_id: str,
    user: CurrentUser,
) -> dict:
    """
    Require user to be the owner of the conversation.

    Returns:
        The conversation data

    Raises:
        HTTPException 404: If conversation not found
        HTTPException 403: If user is not the owner
    """
    conversation_service = get_conversation_service()
    conversation = await conversation_service.get_conversation(
        conversation_id, user.id
    )

    if not conversation:
        # Check if conversation exists at all
        from app.db.supabase import get_supabase_admin_client
        client = get_supabase_admin_client()
        result = client.table("conversations").select("id").eq("id", conversation_id).maybe_single().execute()

        if result.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can perform this action",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

    return conversation
