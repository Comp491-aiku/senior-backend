"""
Chat message model for conversational interface
"""
from sqlalchemy import Column, String, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class PlanningMode(str, enum.Enum):
    PLAN = "plan"
    AUTO_PAY = "auto-pay"
    EDIT = "edit"


class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=True)

    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)

    # Planning mode when message was sent
    planning_mode = Column(Enum(PlanningMode), nullable=True)

    # Agent activity data (for assistant messages)
    agent_activity = Column(JSONB, nullable=True)

    # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    message_metadata = Column(JSONB, default={})

    # Relationships
    user = relationship("User", backref="chat_messages")
    trip = relationship("Trip", backref="chat_messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, user_id={self.user_id})>"
