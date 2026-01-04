"""
Todo Database Model

Handles trip todos in Supabase.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.db.supabase import get_supabase_admin_client


class TodoService:
    """
    Service for managing trip todos in Supabase.

    Tables required:
    - trip_todos: id, conversation_id, created_by, assigned_to, title,
      description, due_date, priority, status, category, linked_result_id,
      position, completed_at, completed_by, created_at, updated_at
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_admin_client()
        return self._client

    async def create_todo(
        self,
        conversation_id: str,
        created_by: str,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: str = "medium",
        category: Optional[str] = None,
        assigned_to: Optional[str] = None,
        linked_result_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new todo for a trip conversation.

        Args:
            conversation_id: The conversation this todo belongs to
            created_by: User ID of creator
            title: Todo title
            description: Optional description
            due_date: Optional due date (YYYY-MM-DD)
            priority: 'low', 'medium', or 'high'
            category: Optional category
            assigned_to: Optional user ID to assign to
            linked_result_id: Optional travel result to link to

        Returns:
            The created todo record
        """
        todo_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # Get next position
        position = await self._get_next_position(conversation_id)

        data = {
            "id": todo_id,
            "conversation_id": conversation_id,
            "created_by": created_by,
            "title": title,
            "priority": priority,
            "status": "pending",
            "position": position,
            "created_at": now,
            "updated_at": now,
        }

        if description:
            data["description"] = description
        if due_date:
            data["due_date"] = due_date
        if category:
            data["category"] = category
        if assigned_to:
            data["assigned_to"] = assigned_to
        if linked_result_id:
            data["linked_result_id"] = linked_result_id

        result = self.client.table("trip_todos").insert(data).execute()

        if result.data:
            todo = result.data[0]
            # Enrich with user info
            todo = await self._enrich_todo(todo)
            return todo
        return data

    async def get_todos(
        self,
        conversation_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all todos for a conversation with optional filters."""
        query = (
            self.client.table("trip_todos")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("position", desc=False)
        )

        if status:
            query = query.eq("status", status)
        if priority:
            query = query.eq("priority", priority)
        if assigned_to:
            query = query.eq("assigned_to", assigned_to)

        result = query.execute()
        todos = result.data or []

        # Enrich with user info
        for todo in todos:
            todo = await self._enrich_todo(todo)

        return todos

    async def get_todo(
        self,
        todo_id: str,
        conversation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific todo by ID."""
        result = (
            self.client.table("trip_todos")
            .select("*")
            .eq("id", todo_id)
            .eq("conversation_id", conversation_id)
            .single()
            .execute()
        )

        if result.data:
            return await self._enrich_todo(result.data)
        return None

    async def update_todo(
        self,
        todo_id: str,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a todo."""
        update_data = {"updated_at": datetime.utcnow().isoformat()}

        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if due_date is not None:
            update_data["due_date"] = due_date if due_date else None
        if priority is not None:
            update_data["priority"] = priority
        if category is not None:
            update_data["category"] = category if category else None
        if assigned_to is not None:
            update_data["assigned_to"] = assigned_to if assigned_to else None

        # Handle status changes
        if status is not None:
            update_data["status"] = status
            if status == "completed":
                update_data["completed_at"] = datetime.utcnow().isoformat()
                update_data["completed_by"] = user_id
            elif status in ("pending", "in_progress"):
                # Clear completion info if status is reverted
                update_data["completed_at"] = None
                update_data["completed_by"] = None

        result = (
            self.client.table("trip_todos")
            .update(update_data)
            .eq("id", todo_id)
            .eq("conversation_id", conversation_id)
            .execute()
        )

        if result.data:
            return await self._enrich_todo(result.data[0])
        return None

    async def delete_todo(
        self,
        todo_id: str,
        conversation_id: str,
    ) -> bool:
        """Delete a todo."""
        result = (
            self.client.table("trip_todos")
            .delete()
            .eq("id", todo_id)
            .eq("conversation_id", conversation_id)
            .execute()
        )

        return bool(result.data)

    async def reorder_todos(
        self,
        conversation_id: str,
        todo_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """Reorder todos by updating their positions."""
        updated = []
        now = datetime.utcnow().isoformat()

        for position, todo_id in enumerate(todo_ids):
            result = (
                self.client.table("trip_todos")
                .update({"position": position, "updated_at": now})
                .eq("id", todo_id)
                .eq("conversation_id", conversation_id)
                .execute()
            )
            if result.data:
                updated.append(result.data[0])

        return updated

    async def toggle_todo(
        self,
        todo_id: str,
        conversation_id: str,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Toggle a todo's completion status."""
        todo = await self.get_todo(todo_id, conversation_id)
        if not todo:
            return None

        new_status = "pending" if todo["status"] == "completed" else "completed"
        return await self.update_todo(
            todo_id=todo_id,
            conversation_id=conversation_id,
            user_id=user_id,
            status=new_status,
        )

    async def get_todo_stats(
        self,
        conversation_id: str,
    ) -> Dict[str, int]:
        """Get todo statistics for a conversation."""
        result = (
            self.client.table("trip_todos")
            .select("status")
            .eq("conversation_id", conversation_id)
            .execute()
        )

        todos = result.data or []
        stats = {
            "total": len(todos),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "cancelled": 0,
        }

        for todo in todos:
            status = todo.get("status", "pending")
            if status in stats:
                stats[status] += 1

        return stats

    async def _get_next_position(self, conversation_id: str) -> int:
        """Get the next position for a new todo."""
        result = (
            self.client.table("trip_todos")
            .select("position")
            .eq("conversation_id", conversation_id)
            .order("position", desc=True)
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]["position"] + 1
        return 0

    async def _enrich_todo(self, todo: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich todo with user info."""
        if todo.get("created_by"):
            creator = await self._get_user_info(todo["created_by"])
            if creator:
                todo["creator"] = creator

        if todo.get("assigned_to"):
            assignee = await self._get_user_info(todo["assigned_to"])
            if assignee:
                todo["assignee"] = assignee

        if todo.get("completed_by"):
            completer = await self._get_user_info(todo["completed_by"])
            if completer:
                todo["completer"] = completer

        return todo

    async def _get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user info from auth.users."""
        try:
            user = self.client.auth.admin.get_user_by_id(user_id)
            if user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "name": user.user.user_metadata.get("full_name")
                    or user.user.user_metadata.get("name"),
                    "avatar_url": user.user.user_metadata.get("avatar_url"),
                }
        except Exception:
            pass
        return None


# Singleton instance
_todo_service: Optional[TodoService] = None


def get_todo_service() -> TodoService:
    """Get the todo service singleton."""
    global _todo_service
    if _todo_service is None:
        _todo_service = TodoService()
    return _todo_service
