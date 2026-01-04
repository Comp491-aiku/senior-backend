"""
Chat API Endpoints

Handles chat interactions with the travel agent.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import logging

from app.core.security import CurrentUser, get_current_user
from app.api.schemas import ChatRequest, ChatResponse
from app.agentic import get_orchestrator, ConversationHistory
from app.db import get_conversation_service, get_message_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Send a message and receive streaming response via SSE.

    Returns a Server-Sent Events stream with the following event types:
    - thinking: Agent is processing
    - tool_start: Starting tool execution
    - tool_end: Tool execution complete
    - message: Final response text
    - complete: Stream complete
    - error: An error occurred
    """
    conversation_service = get_conversation_service()
    message_service = get_message_service()
    orchestrator = get_orchestrator()

    # Get or create conversation
    conversation_id = request.conversation_id

    if conversation_id:
        # Verify conversation exists and belongs to user
        conv = await conversation_service.get_conversation(conversation_id, user.id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation
        conv = await conversation_service.create_conversation(
            user_id=user.id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
        )
        conversation_id = conv["id"]

    # Load existing messages
    existing_messages = await message_service.get_messages(conversation_id)

    # Create conversation history from existing messages
    history = ConversationHistory(conversation_id=conversation_id, user_id=user.id)
    for msg in existing_messages:
        if msg["role"] == "user":
            history.add_user_message(msg["content"])
        elif msg["role"] == "assistant":
            history.add_assistant_message(
                content=msg["content"],
                tool_calls=msg.get("tool_calls"),
            )
        elif msg["role"] == "tool":
            history.add_tool_result(
                tool_call_id=msg.get("tool_call_id", ""),
                content=msg["content"],
            )

    async def event_stream():
        """Generate SSE events."""
        try:
            async for event in orchestrator.run_stream(request.message, history):
                yield event

            # Save messages to database after completion
            for msg in history.messages[len(existing_messages):]:
                await message_service.add_message(
                    conversation_id=conversation_id,
                    role=msg.role,
                    content=msg.content,
                    tool_calls=msg.tool_calls,
                    tool_call_id=msg.tool_call_id,
                )

        except Exception as e:
            logger.exception("Error in chat stream")
            yield f"event: error\ndata: {{\"error\": \"{str(e)}\"}}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Conversation-Id": conversation_id,
        },
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Send a message and receive response (non-streaming).

    For streaming responses, use POST /chat/stream instead.
    """
    conversation_service = get_conversation_service()
    message_service = get_message_service()
    orchestrator = get_orchestrator()

    # Get or create conversation
    conversation_id = request.conversation_id

    if conversation_id:
        conv = await conversation_service.get_conversation(conversation_id, user.id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = await conversation_service.create_conversation(
            user_id=user.id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
        )
        conversation_id = conv["id"]

    # Load existing messages
    existing_messages = await message_service.get_messages(conversation_id)

    # Create conversation history
    history = ConversationHistory(conversation_id=conversation_id, user_id=user.id)
    for msg in existing_messages:
        if msg["role"] == "user":
            history.add_user_message(msg["content"])
        elif msg["role"] == "assistant":
            history.add_assistant_message(
                content=msg["content"],
                tool_calls=msg.get("tool_calls"),
            )
        elif msg["role"] == "tool":
            history.add_tool_result(
                tool_call_id=msg.get("tool_call_id", ""),
                content=msg["content"],
            )

    # Run orchestration
    response = await orchestrator.run(request.message, history)

    # Save new messages to database
    for msg in history.messages[len(existing_messages):]:
        await message_service.add_message(
            conversation_id=conversation_id,
            role=msg.role,
            content=msg.content,
            tool_calls=msg.tool_calls,
            tool_call_id=msg.tool_call_id,
        )

    from datetime import datetime

    return ChatResponse(
        conversation_id=conversation_id,
        message=response,
        created_at=datetime.utcnow(),
    )
