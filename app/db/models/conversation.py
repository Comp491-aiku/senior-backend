"""
Conversation Database Model

Handles conversation and message storage in Supabase.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json

from app.db.supabase import get_supabase_admin_client


class ConversationService:
    """
    Service for managing conversations in Supabase.

    Tables required in Supabase:
    - conversations: id, user_id, title, created_at, updated_at
    - messages: id, conversation_id, role, content, tool_calls, tool_call_id, created_at
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_admin_client()
        return self._client

    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        data = {
            "id": conversation_id,
            "user_id": user_id,
            "title": title or "New Conversation",
            "created_at": now,
            "updated_at": now,
        }

        result = self.client.table("conversations").insert(data).execute()

        if result.data:
            return result.data[0]
        return data

    async def get_conversation(
        self,
        conversation_id: str,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID (with user authorization check)."""
        result = (
            self.client.table("conversations")
            .select("*")
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        return result.data if result.data else None

    async def list_conversations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List conversations for a user."""
        result = (
            self.client.table("conversations")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return result.data or []

    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a conversation."""
        update_data = {"updated_at": datetime.utcnow().isoformat()}

        if title:
            update_data["title"] = title

        result = (
            self.client.table("conversations")
            .update(update_data)
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .execute()
        )

        return result.data[0] if result.data else None

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str,
    ) -> bool:
        """Delete a conversation and its messages."""
        # Delete messages first (due to foreign key)
        self.client.table("messages").delete().eq(
            "conversation_id", conversation_id
        ).execute()

        # Delete conversation
        result = (
            self.client.table("conversations")
            .delete()
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .execute()
        )

        return bool(result.data)


class MessageService:
    """Service for managing messages in Supabase."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_admin_client()
        return self._client

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a message to a conversation."""
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        data = {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "tool_calls": json.dumps(tool_calls) if tool_calls else None,
            "tool_call_id": tool_call_id,
            "created_at": now,
        }

        result = self.client.table("messages").insert(data).execute()

        # Update conversation updated_at
        self.client.table("conversations").update(
            {"updated_at": now}
        ).eq("id", conversation_id).execute()

        if result.data:
            msg = result.data[0]
            if msg.get("tool_calls"):
                msg["tool_calls"] = json.loads(msg["tool_calls"])
            return msg

        return data

    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        result = (
            self.client.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )

        messages = result.data or []

        # Parse tool_calls JSON
        for msg in messages:
            if msg.get("tool_calls"):
                try:
                    msg["tool_calls"] = json.loads(msg["tool_calls"])
                except (json.JSONDecodeError, TypeError):
                    pass

        return messages

    async def delete_messages(self, conversation_id: str) -> bool:
        """Delete all messages in a conversation."""
        result = (
            self.client.table("messages")
            .delete()
            .eq("conversation_id", conversation_id)
            .execute()
        )

        return True


# Singleton instances
_conversation_service: Optional[ConversationService] = None
_message_service: Optional[MessageService] = None


def get_conversation_service() -> ConversationService:
    """Get the conversation service singleton."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service


def get_message_service() -> MessageService:
    """Get the message service singleton."""
    global _message_service
    if _message_service is None:
        _message_service = MessageService()
    return _message_service
