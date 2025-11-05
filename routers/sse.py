"""
Server-Sent Events (SSE) endpoints for real-time agent activity streaming
"""
import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from models.user import User
from auth.dependencies import get_current_user
from agents.orchestrator_agent import OrchestratorAgent

router = APIRouter()


async def agent_activity_stream(
    message: str,
    planning_mode: str,
    trip_id: str = None,
    user_id: str = None
) -> AsyncGenerator[str, None]:
    """
    Stream agent activity in real-time using SSE

    Yields:
        Server-sent events with agent activity updates
    """
    try:
        # Prepare context for orchestrator
        context = {
            "user_id": user_id,
            "trip_id": trip_id,
            "message": message,
            "planning_mode": planning_mode,
            "stream": True,  # Enable streaming mode
        }

        # Create orchestrator
        orchestrator = OrchestratorAgent()

        # Stream agent activity
        async for activity in orchestrator.stream_execution(context):
            # Format as SSE event
            event_data = {
                "agent": activity.get("agent"),
                "status": activity.get("status"),
                "message": activity.get("message"),
                "progress": activity.get("progress"),
                "data": activity.get("data"),
            }

            # Send event
            yield f"data: {json.dumps(event_data)}\n\n"

            # Small delay to prevent overwhelming client
            await asyncio.sleep(0.1)

        # Send completion event
        yield f"data: {json.dumps({'status': 'completed'})}\n\n"

    except Exception as e:
        # Send error event
        error_data = {
            "status": "error",
            "message": str(e)
        }
        yield f"data: {json.dumps(error_data)}\n\n"


@router.get("/stream/agent-activity")
async def stream_agent_activity(
    message: str,
    planning_mode: str = "plan",
    trip_id: str = None,
    current_user: User = Depends(get_current_user),
):
    """
    Stream real-time agent activity using Server-Sent Events

    This endpoint provides a real-time stream of agent activity as the
    orchestrator coordinates different AI agents.

    Args:
        message: User's input message
        planning_mode: Planning mode (plan, auto-pay, edit)
        trip_id: Optional trip ID
        current_user: Authenticated user

    Returns:
        SSE stream with agent activity updates
    """
    return StreamingResponse(
        agent_activity_stream(
            message=message,
            planning_mode=planning_mode,
            trip_id=trip_id,
            user_id=str(current_user.id)
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
