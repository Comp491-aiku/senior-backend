"""
Todo Tools

Tools for AI to manage trip todos.
"""

from typing import Any, Dict, Optional, List
import json

from app.agentic.tools.base import BaseTool
from app.agentic.tools.types import ToolResult, ToolResultStatus, ToolType
from app.db.models.todos import get_todo_service


class CreateTodoTool(BaseTool):
    """
    Create a todo item for trip planning.

    This tool allows the AI to create todos based on the conversation context,
    such as things to pack, bookings to make, or places to visit.
    """

    # Mark this tool as needing context injection
    needs_context = True

    @property
    def name(self) -> str:
        return "create_todo"

    @property
    def description(self) -> str:
        return (
            "Create a todo/task for the trip. Use this when the user asks to add tasks, "
            "create a to-do list, or when you identify action items for the trip. "
            "Examples: 'Add packing list', 'Create todos for the trip', "
            "'What should I prepare?', 'Make a checklist'. "
            "You can create multiple todos by calling this tool multiple times."
        )

    @property
    def tool_type(self) -> ToolType:
        return ToolType.WRITE

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short title for the todo (e.g., 'Book hotel', 'Pack sunscreen')"
                },
                "description": {
                    "type": "string",
                    "description": "Optional longer description with details"
                },
                "due_date": {
                    "type": "string",
                    "description": "Optional due date in YYYY-MM-DD format"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Priority level (default: medium)"
                },
                "category": {
                    "type": "string",
                    "description": "Category like 'packing', 'booking', 'documents', 'activities', 'transportation'"
                },
            },
            "required": ["title"]
        }

    async def execute(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: str = "medium",
        category: Optional[str] = None,
        # Context injected by orchestrator
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """Create a todo for the trip."""
        if not conversation_id or not user_id:
            return ToolResult(
                output="",
                error="Missing context: conversation_id or user_id not provided",
                status=ToolResultStatus.ERROR,
            )

        try:
            service = get_todo_service()
            todo = await service.create_todo(
                conversation_id=conversation_id,
                created_by=user_id,
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                category=category,
            )

            return ToolResult(
                output=json.dumps({
                    "success": True,
                    "todo": {
                        "id": todo.get("id"),
                        "title": todo.get("title"),
                        "priority": todo.get("priority"),
                        "category": todo.get("category"),
                    },
                    "message": f"Created todo: {title}"
                }, ensure_ascii=False),
                status=ToolResultStatus.SUCCESS,
                data={
                    "id": todo.get("id"),
                    "title": todo.get("title"),
                    "priority": todo.get("priority"),
                    "category": todo.get("category"),
                }
            )
        except Exception as e:
            return ToolResult(
                output="",
                error=f"Failed to create todo: {str(e)}",
                status=ToolResultStatus.ERROR,
            )


class CreateMultipleTodosTool(BaseTool):
    """
    Create multiple todos at once for trip planning.

    More efficient than calling create_todo multiple times.
    """

    needs_context = True

    @property
    def name(self) -> str:
        return "create_multiple_todos"

    @property
    def description(self) -> str:
        return (
            "Create multiple todos at once. Use this when you need to add several tasks, "
            "like a complete packing list or a full trip checklist. "
            "More efficient than creating todos one by one."
        )

    @property
    def tool_type(self) -> ToolType:
        return ToolType.WRITE

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Short title for the todo"
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional description"
                            },
                            "due_date": {
                                "type": "string",
                                "description": "Optional due date (YYYY-MM-DD)"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"]
                            },
                            "category": {
                                "type": "string",
                                "description": "Category like 'packing', 'booking', 'documents'"
                            },
                        },
                        "required": ["title"]
                    },
                    "description": "List of todos to create"
                }
            },
            "required": ["todos"]
        }

    async def execute(
        self,
        todos: List[Dict[str, Any]],
        # Context injected by orchestrator
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """Create multiple todos for the trip."""
        if not conversation_id or not user_id:
            return ToolResult(
                output="",
                error="Missing context: conversation_id or user_id not provided",
                status=ToolResultStatus.ERROR,
            )

        try:
            service = get_todo_service()
            created_todos = []

            for todo_data in todos:
                todo = await service.create_todo(
                    conversation_id=conversation_id,
                    created_by=user_id,
                    title=todo_data.get("title", ""),
                    description=todo_data.get("description"),
                    due_date=todo_data.get("due_date"),
                    priority=todo_data.get("priority", "medium"),
                    category=todo_data.get("category"),
                )
                created_todos.append({
                    "id": todo.get("id"),
                    "title": todo.get("title"),
                    "priority": todo.get("priority"),
                    "category": todo.get("category"),
                })

            return ToolResult(
                output=json.dumps({
                    "success": True,
                    "count": len(created_todos),
                    "todos": created_todos,
                    "message": f"Created {len(created_todos)} todos"
                }, ensure_ascii=False),
                status=ToolResultStatus.SUCCESS,
                data={
                    "count": len(created_todos),
                    "todos": created_todos,
                }
            )
        except Exception as e:
            return ToolResult(
                output="",
                error=f"Failed to create todos: {str(e)}",
                status=ToolResultStatus.ERROR,
            )


def get_todo_tools() -> List[BaseTool]:
    """Get all todo-related tools."""
    return [
        CreateTodoTool(),
        CreateMultipleTodosTool(),
    ]
