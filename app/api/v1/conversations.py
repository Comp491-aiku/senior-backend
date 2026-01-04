"""
Conversations API Endpoints

CRUD operations for conversations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from app.core.security import CurrentUser, get_current_user
from app.core.permissions import check_conversation_access, Permission
from app.api.schemas import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    MessagesResponse,
    MessageResponse,
)
from app.db import get_conversation_service, get_message_service

router = APIRouter(prefix="/conversations", tags=["Conversations"])


def _parse_datetime(dt_str: Optional[str]) -> datetime:
    """Parse datetime string to datetime object."""
    if not dt_str:
        return datetime.utcnow()
    try:
        # Handle ISO format with or without timezone
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return datetime.utcnow()


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    user: CurrentUser = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all conversations for the current user."""
    service = get_conversation_service()
    conversations = await service.list_conversations(
        user_id=user.id,
        limit=limit,
        offset=offset,
    )

    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                id=c["id"],
                user_id=c["user_id"],
                title=c["title"],
                created_at=_parse_datetime(c.get("created_at")),
                updated_at=_parse_datetime(c.get("updated_at")),
            )
            for c in conversations
        ],
        total=len(conversations),
    )


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    user: CurrentUser = Depends(get_current_user),
):
    """Create a new conversation."""
    service = get_conversation_service()
    conversation = await service.create_conversation(
        user_id=user.id,
        title=request.title,
    )

    return ConversationResponse(
        id=conversation["id"],
        user_id=conversation["user_id"],
        title=conversation["title"],
        created_at=_parse_datetime(conversation.get("created_at")),
        updated_at=_parse_datetime(conversation.get("updated_at")),
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Get a specific conversation (owner or shared user)."""
    # Use permission check to allow shared users
    conversation, _ = await check_conversation_access(
        conversation_id, user, Permission.VIEW
    )

    return ConversationResponse(
        id=conversation["id"],
        user_id=conversation["user_id"],
        title=conversation["title"],
        created_at=_parse_datetime(conversation.get("created_at")),
        updated_at=_parse_datetime(conversation.get("updated_at")),
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """Update a conversation (e.g., rename)."""
    service = get_conversation_service()

    # Check if exists
    existing = await service.get_conversation(conversation_id, user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Conversation not found")

    updated = await service.update_conversation(
        conversation_id=conversation_id,
        user_id=user.id,
        title=request.title,
    )

    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update conversation")

    return ConversationResponse(
        id=updated["id"],
        user_id=updated["user_id"],
        title=updated["title"],
        created_at=_parse_datetime(updated.get("created_at")),
        updated_at=_parse_datetime(updated.get("updated_at")),
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Delete a conversation and all its messages."""
    service = get_conversation_service()

    # Check if exists
    existing = await service.get_conversation(conversation_id, user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await service.delete_conversation(conversation_id, user.id)

    return {"message": "Conversation deleted"}


@router.get("/{conversation_id}/messages", response_model=MessagesResponse)
async def get_messages(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500),
):
    """Get all messages in a conversation."""
    conversation_service = get_conversation_service()
    message_service = get_message_service()

    # Check if conversation exists and belongs to user
    conversation = await conversation_service.get_conversation(conversation_id, user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await message_service.get_messages(conversation_id, limit=limit)

    return MessagesResponse(
        messages=[
            MessageResponse(
                id=m["id"],
                conversation_id=m["conversation_id"],
                role=m["role"],
                content=m["content"],
                tool_calls=m.get("tool_calls"),
                tool_call_id=m.get("tool_call_id"),
                created_at=_parse_datetime(m.get("created_at")),
            )
            for m in messages
        ]
    )
