"""
Shares API Endpoints

Manage conversation sharing and collaboration.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from app.core.security import CurrentUser, get_current_user, get_optional_user
from app.core.permissions import require_owner, Permission
from app.api.schemas import (
    ShareCreate,
    ShareUpdate,
    ShareResponse,
    ShareListResponse,
    SharedUserResponse,
    SharedConversationResponse,
    SharedWithMeResponse,
    ConversationResponse,
)
from app.db.models.sharing import get_share_service
from app.config import settings

router = APIRouter(tags=["Shares"])


def _parse_datetime(dt_str: Optional[str]) -> datetime:
    """Parse datetime string to datetime object."""
    if not dt_str:
        return datetime.utcnow()
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return datetime.utcnow()


def _build_share_link(token: str) -> str:
    """Build the full share link URL."""
    base_url = settings.FRONTEND_URL or "http://localhost:3000"
    return f"{base_url}/shared/{token}"


def _share_to_response(share: dict) -> ShareResponse:
    """Convert share dict to response model."""
    shared_user = None
    if share.get("shared_user"):
        u = share["shared_user"]
        shared_user = SharedUserResponse(
            id=u["id"],
            email=u.get("email"),
            name=u.get("name"),
            avatar_url=u.get("avatar_url"),
        )

    share_link = None
    if share.get("share_token"):
        share_link = _build_share_link(share["share_token"])

    return ShareResponse(
        id=share["id"],
        conversation_id=share["conversation_id"],
        permission=share["permission"],
        shared_with_email=share.get("shared_with_email"),
        share_link=share_link,
        share_token=share.get("share_token"),
        accepted=share.get("accepted_at") is not None,
        shared_user=shared_user,
        created_at=_parse_datetime(share.get("created_at")),
        updated_at=_parse_datetime(share.get("updated_at")),
    )


# =====================
# Conversation Shares
# =====================

@router.post(
    "/conversations/{conversation_id}/shares",
    response_model=ShareResponse,
)
async def create_share(
    conversation_id: str,
    request: ShareCreate,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Create a new share for a conversation.

    Only the conversation owner can create shares.
    """
    # Verify ownership
    await require_owner(conversation_id, user)

    # Validate request
    if not request.email and not request.create_link:
        raise HTTPException(
            status_code=400,
            detail="Must provide either email or create_link=true",
        )

    service = get_share_service()

    # Check for duplicate email share
    if request.email:
        existing_shares = await service.get_shares(conversation_id, user.id)
        for share in existing_shares:
            if (
                share.get("shared_with_email", "").lower()
                == request.email.lower()
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Already shared with this email",
                )

    share = await service.create_share(
        conversation_id=conversation_id,
        owner_id=user.id,
        permission=request.permission,
        shared_with_email=request.email,
        create_link=request.create_link,
        expires_in_days=request.expires_in_days,
    )

    return _share_to_response(share)


@router.get(
    "/conversations/{conversation_id}/shares",
    response_model=ShareListResponse,
)
async def list_shares(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    List all shares for a conversation.

    Only the conversation owner can view shares.
    """
    await require_owner(conversation_id, user)

    service = get_share_service()
    shares = await service.get_shares(conversation_id, user.id)

    return ShareListResponse(
        shares=[_share_to_response(s) for s in shares],
        total=len(shares),
    )


@router.patch(
    "/conversations/{conversation_id}/shares/{share_id}",
    response_model=ShareResponse,
)
async def update_share(
    conversation_id: str,
    share_id: str,
    request: ShareUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Update a share's permission level.

    Only the conversation owner can update shares.
    """
    await require_owner(conversation_id, user)

    service = get_share_service()
    share = await service.update_share(
        share_id=share_id,
        owner_id=user.id,
        permission=request.permission,
    )

    if not share:
        raise HTTPException(status_code=404, detail="Share not found")

    # Re-fetch with user info
    shares = await service.get_shares(conversation_id, user.id)
    for s in shares:
        if s["id"] == share_id:
            return _share_to_response(s)

    return _share_to_response(share)


@router.delete("/conversations/{conversation_id}/shares/{share_id}")
async def revoke_share(
    conversation_id: str,
    share_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Revoke a share (delete it).

    Only the conversation owner can revoke shares.
    """
    await require_owner(conversation_id, user)

    service = get_share_service()
    success = await service.revoke_share(share_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Share not found")

    return {"message": "Share revoked"}


# =====================
# Shared With Me
# =====================

@router.get("/shares/shared-with-me", response_model=SharedWithMeResponse)
async def get_shared_with_me(
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get all conversations shared with the current user.

    Returns both accepted shares and pending invitations.
    """
    service = get_share_service()
    all_shares = await service.get_shared_with_me(user.id, user.email)

    shared = []
    pending = []

    for share in all_shares:
        conv_data = share.get("conversations", {})
        owner_data = share.get("owner", {})

        if not conv_data:
            continue

        item = SharedConversationResponse(
            id=share["id"],
            conversation_id=share["conversation_id"],
            permission=share["permission"],
            accepted=share.get("accepted_at") is not None,
            conversation=ConversationResponse(
                id=conv_data["id"],
                user_id=conv_data["user_id"],
                title=conv_data["title"],
                created_at=_parse_datetime(conv_data.get("created_at")),
                updated_at=_parse_datetime(conv_data.get("updated_at")),
            ),
            owner=SharedUserResponse(
                id=owner_data.get("id", ""),
                email=owner_data.get("email"),
                name=owner_data.get("name"),
                avatar_url=owner_data.get("avatar_url"),
            ),
            created_at=_parse_datetime(share.get("created_at")),
        )

        if share.get("accepted_at"):
            shared.append(item)
        else:
            pending.append(item)

    return SharedWithMeResponse(
        shared=shared,
        pending=pending,
        total=len(shared) + len(pending),
    )


@router.post("/shares/{share_id}/accept")
async def accept_share(
    share_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Accept a share invitation.
    """
    service = get_share_service()
    share = await service.accept_invitation(
        share_id=share_id,
        user_id=user.id,
        user_email=user.email,
    )

    if not share:
        raise HTTPException(
            status_code=404,
            detail="Invitation not found or not for this user",
        )

    return {"message": "Invitation accepted", "conversation_id": share["conversation_id"]}


@router.post("/shares/{share_id}/decline")
async def decline_share(
    share_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Decline a share invitation (removes it).
    """
    service = get_share_service()

    # Get the share to verify it's for this user
    shares = await service.get_shared_with_me(user.id, user.email)
    share = next((s for s in shares if s["id"] == share_id), None)

    if not share:
        raise HTTPException(
            status_code=404,
            detail="Invitation not found",
        )

    # Delete the share using admin client
    from app.db.supabase import get_supabase_admin_client
    client = get_supabase_admin_client()
    client.table("conversation_shares").delete().eq("id", share_id).execute()

    return {"message": "Invitation declined"}


# =====================
# Public Share Link
# =====================

@router.get("/shares/link/{token}")
async def get_share_by_token(
    token: str,
    user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """
    Access a conversation via share token.

    Returns conversation info. Full access requires authentication.
    """
    service = get_share_service()
    share = await service.validate_share_token(token)

    if not share:
        raise HTTPException(
            status_code=404,
            detail="Invalid or expired share link",
        )

    conv_data = share.get("conversations", {})

    response = {
        "conversation_id": share["conversation_id"],
        "permission": share["permission"],
        "title": conv_data.get("title", "Shared Trip"),
        "authenticated": user is not None,
    }

    # If user is authenticated, they can access the full conversation
    if user:
        response["can_access"] = True

        # Auto-accept if user is logged in and not already a member
        existing_permission = await service.get_user_permission(
            share["conversation_id"], user.id
        )
        if not existing_permission:
            # Create a share entry for this user
            await service.create_share(
                conversation_id=share["conversation_id"],
                owner_id=share["owner_id"],
                permission=share["permission"],
                shared_with_email=user.email,
            )
            # Accept it immediately
            shares = await service.get_shared_with_me(user.id, user.email)
            for s in shares:
                if s["conversation_id"] == share["conversation_id"]:
                    await service.accept_invitation(s["id"], user.id, user.email)
                    break
    else:
        response["can_access"] = False
        response["message"] = "Login to access this shared trip"

    return response
