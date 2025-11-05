"""
Chat endpoints for conversational trip planning
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from models.user import User
from models.chat_message import ChatMessage, MessageRole, PlanningMode
from models.trip import Trip
from schemas.chat import ChatRequest, ChatResponse, ChatHistory, ChatMessageResponse, AgentActivity
from auth.dependencies import get_current_user
from agents.orchestrator_agent import OrchestratorAgent
from datetime import datetime

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get AI response

    This endpoint handles conversational trip planning:
    - Takes natural language input (text or voice)
    - Uses orchestrator to coordinate AI agents
    - Returns AI response with real-time agent activity
    - Supports three planning modes: plan, auto-pay, edit

    Args:
        request: Chat message request
        current_user: Authenticated user
        db: Database session

    Returns:
        AI response with agent activity
    """
    # Save user message to database
    user_message = ChatMessage(
        user_id=current_user.id,
        trip_id=request.trip_id,
        role=MessageRole.USER,
        content=request.message,
        planning_mode=PlanningMode(request.planning_mode),
        metadata={"voice_input": request.voice_input}
    )
    db.add(user_message)
    db.commit()

    # Get or create trip
    trip = None
    if request.trip_id:
        trip = db.query(Trip).filter(
            Trip.id == request.trip_id,
            Trip.user_id == current_user.id
        ).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )

    # Prepare context for orchestrator
    context = {
        "user_id": str(current_user.id),
        "trip_id": request.trip_id,
        "message": request.message,
        "planning_mode": request.planning_mode,
        "chat_history": await get_recent_chat_history(current_user.id, request.trip_id, db),
    }

    # Execute orchestrator agent
    orchestrator = OrchestratorAgent()
    agent_result = await orchestrator.execute(context)

    # Extract AI response and agent activity
    ai_content = agent_result.get("response", "I'm processing your request...")
    agent_activities = agent_result.get("agent_activity", [])

    # Convert agent activities to schema format
    formatted_activities = [
        AgentActivity(
            agent=activity.get("agent", "Unknown"),
            status=activity.get("status", "completed"),
            message=activity.get("message", ""),
            progress=activity.get("progress"),
            data=activity.get("data")
        )
        for activity in agent_activities
    ]

    # Save assistant message to database
    assistant_message = ChatMessage(
        user_id=current_user.id,
        trip_id=request.trip_id or agent_result.get("trip_id"),
        role=MessageRole.ASSISTANT,
        content=ai_content,
        planning_mode=PlanningMode(request.planning_mode),
        agent_activity=[activity.dict() for activity in formatted_activities]
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        message_id=str(assistant_message.id),
        content=ai_content,
        agent_activity=formatted_activities,
        trip_id=request.trip_id or agent_result.get("trip_id"),
        created_at=assistant_message.created_at
    )


@router.get("/chat/history", response_model=ChatHistory)
async def get_chat_history(
    trip_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat history for current user

    Args:
        trip_id: Optional trip ID to filter messages
        limit: Maximum number of messages to return
        offset: Number of messages to skip
        current_user: Authenticated user
        db: Database session

    Returns:
        Chat history with messages
    """
    query = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id)

    if trip_id:
        query = query.filter(ChatMessage.trip_id == trip_id)

    total = query.count()
    messages = query.order_by(ChatMessage.created_at.desc()).offset(offset).limit(limit).all()

    # Convert to response schema
    message_responses = [
        ChatMessageResponse(
            id=str(msg.id),
            role=msg.role.value,
            content=msg.content,
            planning_mode=msg.planning_mode.value if msg.planning_mode else None,
            agent_activity=[AgentActivity(**activity) for activity in (msg.agent_activity or [])],
            created_at=msg.created_at
        )
        for msg in reversed(messages)  # Reverse to show oldest first
    ]

    return ChatHistory(
        messages=message_responses,
        total=total,
        trip_id=trip_id
    )


async def get_recent_chat_history(user_id: str, trip_id: Optional[str], db: Session, limit: int = 10) -> list:
    """
    Helper function to get recent chat history for context

    Args:
        user_id: User ID
        trip_id: Optional trip ID
        db: Database session
        limit: Number of recent messages

    Returns:
        List of recent messages
    """
    query = db.query(ChatMessage).filter(ChatMessage.user_id == user_id)

    if trip_id:
        query = query.filter(ChatMessage.trip_id == trip_id)

    messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()

    return [
        {
            "role": msg.role.value,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        }
        for msg in reversed(messages)
    ]
