"""
Todos API Endpoints

Manage trip todos for collaborative planning.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.security import CurrentUser, get_current_user
from app.core.permissions import check_conversation_access, Permission
from app.db.models.todos import get_todo_service

router = APIRouter(tags=["Todos"])


# =====================
# Pydantic Models
# =====================

class UserInfo(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD format")
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    category: Optional[str] = Field(
        None, pattern="^(booking|packing|research|transportation|accommodation|activity|other)$"
    )
    assigned_to: Optional[str] = None
    linked_result_id: Optional[str] = None


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD format or empty string to clear")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    category: Optional[str] = None
    assigned_to: Optional[str] = None


class TodoResponse(BaseModel):
    id: str
    conversation_id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: str
    status: str
    category: Optional[str] = None
    position: int
    creator: Optional[UserInfo] = None
    assignee: Optional[UserInfo] = None
    completer: Optional[UserInfo] = None
    linked_result_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TodoListResponse(BaseModel):
    todos: List[TodoResponse]
    total: int
    stats: dict


class ReorderRequest(BaseModel):
    todo_ids: List[str] = Field(..., min_items=1)


# =====================
# Helper Functions
# =====================

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


def _todo_to_response(todo: dict) -> TodoResponse:
    """Convert todo dict to response model."""
    creator = None
    if todo.get("creator"):
        c = todo["creator"]
        creator = UserInfo(
            id=c["id"],
            email=c.get("email"),
            name=c.get("name"),
            avatar_url=c.get("avatar_url"),
        )

    assignee = None
    if todo.get("assignee"):
        a = todo["assignee"]
        assignee = UserInfo(
            id=a["id"],
            email=a.get("email"),
            name=a.get("name"),
            avatar_url=a.get("avatar_url"),
        )

    completer = None
    if todo.get("completer"):
        comp = todo["completer"]
        completer = UserInfo(
            id=comp["id"],
            email=comp.get("email"),
            name=comp.get("name"),
            avatar_url=comp.get("avatar_url"),
        )

    return TodoResponse(
        id=todo["id"],
        conversation_id=todo["conversation_id"],
        title=todo["title"],
        description=todo.get("description"),
        due_date=todo.get("due_date"),
        priority=todo.get("priority", "medium"),
        status=todo.get("status", "pending"),
        category=todo.get("category"),
        position=todo.get("position", 0),
        creator=creator,
        assignee=assignee,
        completer=completer,
        linked_result_id=todo.get("linked_result_id"),
        completed_at=_parse_datetime(todo.get("completed_at")) if todo.get("completed_at") else None,
        created_at=_parse_datetime(todo.get("created_at")),
        updated_at=_parse_datetime(todo.get("updated_at")),
    )


# =====================
# Todo Endpoints
# =====================

@router.get(
    "/conversations/{conversation_id}/todos",
    response_model=TodoListResponse,
)
async def list_todos(
    conversation_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
):
    """
    List all todos for a conversation.

    Requires view permission or higher.
    """
    await check_conversation_access(conversation_id, user, Permission.VIEW)

    service = get_todo_service()
    todos = await service.get_todos(
        conversation_id=conversation_id,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
    )
    stats = await service.get_todo_stats(conversation_id)

    return TodoListResponse(
        todos=[_todo_to_response(t) for t in todos],
        total=len(todos),
        stats=stats,
    )


@router.post(
    "/conversations/{conversation_id}/todos",
    response_model=TodoResponse,
)
async def create_todo(
    conversation_id: str,
    request: TodoCreate,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Create a new todo for a conversation.

    Requires edit permission.
    """
    await check_conversation_access(conversation_id, user, Permission.EDIT)

    service = get_todo_service()
    todo = await service.create_todo(
        conversation_id=conversation_id,
        created_by=user.id,
        title=request.title,
        description=request.description,
        due_date=request.due_date,
        priority=request.priority,
        category=request.category,
        assigned_to=request.assigned_to,
        linked_result_id=request.linked_result_id,
    )

    return _todo_to_response(todo)


@router.get(
    "/conversations/{conversation_id}/todos/{todo_id}",
    response_model=TodoResponse,
)
async def get_todo(
    conversation_id: str,
    todo_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get a specific todo by ID.

    Requires view permission.
    """
    await check_conversation_access(conversation_id, user, Permission.VIEW)

    service = get_todo_service()
    todo = await service.get_todo(todo_id, conversation_id)

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    return _todo_to_response(todo)


@router.patch(
    "/conversations/{conversation_id}/todos/{todo_id}",
    response_model=TodoResponse,
)
async def update_todo(
    conversation_id: str,
    todo_id: str,
    request: TodoUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Update a todo.

    Requires edit permission.
    """
    await check_conversation_access(conversation_id, user, Permission.EDIT)

    service = get_todo_service()
    todo = await service.update_todo(
        todo_id=todo_id,
        conversation_id=conversation_id,
        user_id=user.id,
        title=request.title,
        description=request.description,
        due_date=request.due_date,
        priority=request.priority,
        status=request.status,
        category=request.category,
        assigned_to=request.assigned_to,
    )

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    return _todo_to_response(todo)


@router.delete("/conversations/{conversation_id}/todos/{todo_id}")
async def delete_todo(
    conversation_id: str,
    todo_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Delete a todo.

    Requires edit permission.
    """
    await check_conversation_access(conversation_id, user, Permission.EDIT)

    service = get_todo_service()
    success = await service.delete_todo(todo_id, conversation_id)

    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")

    return {"message": "Todo deleted"}


@router.post(
    "/conversations/{conversation_id}/todos/{todo_id}/toggle",
    response_model=TodoResponse,
)
async def toggle_todo(
    conversation_id: str,
    todo_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Toggle a todo's completion status.

    Requires edit permission.
    """
    await check_conversation_access(conversation_id, user, Permission.EDIT)

    service = get_todo_service()
    todo = await service.toggle_todo(
        todo_id=todo_id,
        conversation_id=conversation_id,
        user_id=user.id,
    )

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    return _todo_to_response(todo)


@router.post("/conversations/{conversation_id}/todos/reorder")
async def reorder_todos(
    conversation_id: str,
    request: ReorderRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Reorder todos by providing the new order of todo IDs.

    Requires edit permission.
    """
    await check_conversation_access(conversation_id, user, Permission.EDIT)

    service = get_todo_service()
    await service.reorder_todos(conversation_id, request.todo_ids)

    return {"message": "Todos reordered"}


@router.get("/conversations/{conversation_id}/todos/stats")
async def get_todo_stats(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get todo statistics for a conversation.

    Requires view permission.
    """
    await check_conversation_access(conversation_id, user, Permission.VIEW)

    service = get_todo_service()
    stats = await service.get_todo_stats(conversation_id)

    return stats
