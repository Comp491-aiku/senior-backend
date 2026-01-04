"""
Conversation History Management

Handles message history for the agentic orchestrator.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # "user", "assistant", "tool"
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM API."""
        msg = {"role": self.role, "content": self.content}

        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls

        return msg

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "role": self.role,
            "content": self.content,
            "tool_call_id": self.tool_call_id,
            "tool_calls": self.tool_calls,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_db_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from database dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            tool_call_id=data.get("tool_call_id"),
            tool_calls=data.get("tool_calls"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
        )


class ConversationHistory:
    """
    Manages conversation history for a single chat session.

    Provides methods to add messages, get history for LLM,
    and serialize/deserialize for storage.
    """

    def __init__(
        self,
        conversation_id: str,
        messages: Optional[List[Message]] = None,
        user_id: Optional[str] = None,
    ):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.messages: List[Message] = messages or []

    def add_user_message(self, content: str) -> Message:
        """Add a user message."""
        msg = Message(role="user", content=content)
        self.messages.append(msg)
        return msg

    def add_assistant_message(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        """Add an assistant message."""
        msg = Message(role="assistant", content=content, tool_calls=tool_calls)
        self.messages.append(msg)
        return msg

    def add_tool_result(self, tool_call_id: str, content: str) -> Message:
        """Add a tool result message."""
        msg = Message(role="tool", content=content, tool_call_id=tool_call_id)
        self.messages.append(msg)
        return msg

    def get_messages_for_llm(self) -> List[Dict[str, Any]]:
        """Get messages in format suitable for LLM API."""
        return [msg.to_dict() for msg in self.messages]

    def get_last_user_message(self) -> Optional[Message]:
        """Get the most recent user message."""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg
        return None

    def get_last_assistant_message(self) -> Optional[Message]:
        """Get the most recent assistant message."""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg
        return None

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "conversation_id": self.conversation_id,
            "messages": [msg.to_db_dict() for msg in self.messages],
        })

    @classmethod
    def from_json(cls, json_str: str) -> "ConversationHistory":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        messages = [Message.from_db_dict(m) for m in data.get("messages", [])]
        return cls(
            conversation_id=data["conversation_id"],
            messages=messages,
        )

    def to_db_format(self) -> List[Dict[str, Any]]:
        """Convert messages to database storage format."""
        return [msg.to_db_dict() for msg in self.messages]

    @classmethod
    def from_db_format(
        cls,
        conversation_id: str,
        messages_data: List[Dict[str, Any]]
    ) -> "ConversationHistory":
        """Create from database format."""
        messages = [Message.from_db_dict(m) for m in messages_data]
        return cls(conversation_id=conversation_id, messages=messages)

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)
