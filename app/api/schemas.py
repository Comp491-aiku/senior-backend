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
