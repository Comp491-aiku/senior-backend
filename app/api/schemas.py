"""
API Schemas

Pydantic models for API request/response.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# Chat Schemas
class ChatRequest(BaseModel):
    """Request to send a chat message."""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat (non-streaming)."""
    conversation_id: str
    message: str
    created_at: datetime


# Conversation Schemas
class ConversationCreate(BaseModel):
    """Request to create a new conversation."""
    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    """Request to update a conversation."""
    title: str = Field(..., min_length=1, max_length=255)


class ConversationResponse(BaseModel):
    """Conversation response."""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """List of conversations."""
    conversations: List[ConversationResponse]
    total: int


# Message Schemas
class MessageResponse(BaseModel):
    """Message response."""
    id: str
    conversation_id: str
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    created_at: datetime


class MessagesResponse(BaseModel):
    """List of messages."""
    messages: List[MessageResponse]


# User Schemas
class UserResponse(BaseModel):
    """Current user response."""
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: Optional[str] = None


# Health Schemas
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str


# Share Schemas
class ShareCreate(BaseModel):
    """Request to create a share."""
    permission: str = Field(
        default="view",
        pattern="^(view|comment|edit)$",
        description="Permission level: view, comment, or edit"
    )
    email: Optional[str] = Field(None, description="Email to invite")
    create_link: bool = Field(False, description="Create a shareable link")
    expires_in_days: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Link expiration in days"
    )


class ShareUpdate(BaseModel):
    """Request to update a share."""
    permission: str = Field(
        ...,
        pattern="^(view|comment|edit)$",
        description="New permission level"
    )


class SharedUserResponse(BaseModel):
    """User info in share response."""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class ShareResponse(BaseModel):
    """Share response."""
    id: str
    conversation_id: str
    permission: str
    shared_with_email: Optional[str] = None
    share_link: Optional[str] = None
    share_token: Optional[str] = None
    accepted: bool
    shared_user: Optional[SharedUserResponse] = None
    created_at: datetime
    updated_at: datetime


class ShareListResponse(BaseModel):
    """List of shares."""
    shares: List[ShareResponse]
    total: int


class SharedConversationResponse(BaseModel):
    """Conversation shared with the user."""
    id: str
    conversation_id: str
    permission: str
    accepted: bool
    conversation: ConversationResponse
    owner: SharedUserResponse
    created_at: datetime


class SharedWithMeResponse(BaseModel):
    """List of conversations shared with user."""
    shared: List[SharedConversationResponse]
    pending: List[SharedConversationResponse]
    total: int
