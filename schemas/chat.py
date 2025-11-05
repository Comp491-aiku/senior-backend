"""
Chat schemas for conversational interface
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AgentActivity(BaseModel):
    """Schema for individual agent activity"""
    agent: str = Field(..., description="Agent name (e.g., 'Orchestrator', 'Flight Agent')")
    status: str = Field(..., description="Status: pending, running, completed, failed")
    message: str = Field(..., description="Activity description")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data from agent")


class ChatRequest(BaseModel):
    """Schema for incoming chat message"""
    message: str = Field(..., min_length=1, max_length=5000)
    planning_mode: str = Field(default="plan", pattern="^(plan|auto-pay|edit)$")
    trip_id: Optional[str] = Field(None, description="Trip ID if continuing existing conversation")
    voice_input: bool = Field(default=False, description="Whether input was from voice")


class ChatResponse(BaseModel):
    """Schema for chat response"""
    message_id: str
    role: str = "assistant"
    content: str
    agent_activity: List[AgentActivity] = []
    trip_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    """Schema for single chat message in history"""
    id: str
    role: str
    content: str
    planning_mode: Optional[str] = None
    agent_activity: Optional[List[AgentActivity]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistory(BaseModel):
    """Schema for chat history"""
    messages: List[ChatMessageResponse]
    total: int
    trip_id: Optional[str] = None
