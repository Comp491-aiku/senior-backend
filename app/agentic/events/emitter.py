"""
Event Emitter for SSE Streaming

Handles Server-Sent Events for real-time updates during orchestration.
Emits structured data that the frontend can render as UI components.
"""

from typing import AsyncGenerator, Optional, Any, Dict, List
from enum import Enum
from dataclasses import dataclass
import json
import asyncio


class EventType(str, Enum):
    """Types of events that can be emitted during orchestration."""

    # Status events
    THINKING = "thinking"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_ERROR = "tool_error"

    # Content events
    MESSAGE = "message"
    MESSAGE_DELTA = "message_delta"

    # Structured result events (for UI rendering)
    FLIGHTS = "flights"           # Flight search results
    HOTELS = "hotels"             # Hotel search results
    WEATHER = "weather"           # Weather information
    TRANSFERS = "transfers"       # Transfer options
    ACTIVITIES = "activities"     # Activities/tours
    EXCHANGE = "exchange"         # Currency exchange rates

    # Flow events
    ITERATION = "iteration"
    COMPLETE = "complete"
    ERROR = "error"


class ResultType(str, Enum):
    """Types of structured results."""
    FLIGHT = "flight"
    HOTEL = "hotel"
    TRANSFER = "transfer"
    ACTIVITY = "activity"
    WEATHER = "weather"
    EXCHANGE = "exchange"


@dataclass
class Event:
    """A single SSE event."""
    type: EventType
    data: Dict[str, Any]
    id: Optional[str] = None

    def to_sse(self) -> str:
        """Format as SSE string."""
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        lines.append(f"event: {self.type.value}")
        lines.append(f"data: {json.dumps(self.data)}")
        lines.append("")  # Empty line to end event
        return "\n".join(lines) + "\n"


class EventEmitter:
    """
    Emits events during orchestration for SSE streaming.

    Usage:
        emitter = EventEmitter()

        # In orchestrator
        await emitter.emit_thinking("Analyzing travel request...")
        await emitter.emit_tool_start("search_flights", {"origin": "IST", ...})
        await emitter.emit_tool_end("search_flights", result)
        await emitter.emit_message("I found 5 flights...")
        await emitter.emit_complete()

        # In endpoint
        async def stream():
            async for event in emitter.events():
                yield event.to_sse()
    """

    def __init__(self):
        self._queue: asyncio.Queue[Optional[Event]] = asyncio.Queue()
        self._closed = False

    async def emit(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Emit an event."""
        if self._closed:
            return
        event = Event(type=event_type, data=data)
        await self._queue.put(event)

    async def emit_thinking(self, message: str) -> None:
        """Emit a thinking status event."""
        await self.emit(EventType.THINKING, {"message": message})

    async def emit_tool_start(self, tool_name: str, parameters: Dict[str, Any]) -> None:
        """Emit tool execution start event."""
        await self.emit(EventType.TOOL_START, {
            "tool": tool_name,
            "parameters": parameters,
        })

    async def emit_tool_end(
        self,
        tool_name: str,
        result: Any,
        success: bool = True
    ) -> None:
        """Emit tool execution end event."""
        await self.emit(EventType.TOOL_END, {
            "tool": tool_name,
            "result": result,
            "success": success,
        })

    async def emit_tool_error(self, tool_name: str, error: str) -> None:
        """Emit tool error event."""
        await self.emit(EventType.TOOL_ERROR, {
            "tool": tool_name,
            "error": error,
        })

    async def emit_message(self, content: str) -> None:
        """Emit a complete message."""
        await self.emit(EventType.MESSAGE, {"content": content})

    async def emit_message_delta(self, delta: str) -> None:
        """Emit a message chunk (for streaming text)."""
        await self.emit(EventType.MESSAGE_DELTA, {"delta": delta})

    # Structured result emitters for UI components
    async def emit_flights(
        self,
        flights: List[Dict[str, Any]],
        search_params: Optional[Dict[str, Any]] = None,
        tool_execution_id: Optional[str] = None,
    ) -> None:
        """Emit flight search results for UI rendering."""
        await self.emit(EventType.FLIGHTS, {
            "type": "flights",
            "count": len(flights),
            "items": flights,
            "search_params": search_params,
            "tool_execution_id": tool_execution_id,
        })

    async def emit_hotels(
        self,
        hotels: List[Dict[str, Any]],
        search_params: Optional[Dict[str, Any]] = None,
        tool_execution_id: Optional[str] = None,
    ) -> None:
        """Emit hotel search results for UI rendering."""
        await self.emit(EventType.HOTELS, {
            "type": "hotels",
            "count": len(hotels),
            "items": hotels,
            "search_params": search_params,
            "tool_execution_id": tool_execution_id,
        })

    async def emit_weather(
        self,
        weather: Dict[str, Any],
        city: str,
        tool_execution_id: Optional[str] = None,
    ) -> None:
        """Emit weather information for UI rendering."""
        await self.emit(EventType.WEATHER, {
            "type": "weather",
            "city": city,
            "data": weather,
            "tool_execution_id": tool_execution_id,
        })

    async def emit_transfers(
        self,
        transfers: List[Dict[str, Any]],
        search_params: Optional[Dict[str, Any]] = None,
        tool_execution_id: Optional[str] = None,
    ) -> None:
        """Emit transfer options for UI rendering."""
        await self.emit(EventType.TRANSFERS, {
            "type": "transfers",
            "count": len(transfers),
            "items": transfers,
            "search_params": search_params,
            "tool_execution_id": tool_execution_id,
        })

    async def emit_activities(
        self,
        activities: List[Dict[str, Any]],
        search_params: Optional[Dict[str, Any]] = None,
        tool_execution_id: Optional[str] = None,
    ) -> None:
        """Emit activities/tours for UI rendering."""
        await self.emit(EventType.ACTIVITIES, {
            "type": "activities",
            "count": len(activities),
            "items": activities,
            "search_params": search_params,
            "tool_execution_id": tool_execution_id,
        })

    async def emit_exchange(
        self,
        exchange_data: Dict[str, Any],
        tool_execution_id: Optional[str] = None,
    ) -> None:
        """Emit currency exchange information for UI rendering."""
        await self.emit(EventType.EXCHANGE, {
            "type": "exchange",
            "data": exchange_data,
            "tool_execution_id": tool_execution_id,
        })

    async def emit_iteration(self, iteration: int, max_iterations: int) -> None:
        """Emit iteration progress."""
        await self.emit(EventType.ITERATION, {
            "current": iteration,
            "max": max_iterations,
        })

    async def emit_complete(self, message: Optional[str] = None) -> None:
        """Emit completion event and close the emitter."""
        await self.emit(EventType.COMPLETE, {"message": message or "Done"})
        await self.close()

    async def emit_error(self, error: str) -> None:
        """Emit error event and close the emitter."""
        await self.emit(EventType.ERROR, {"error": error})
        await self.close()

    async def close(self) -> None:
        """Close the event emitter."""
        self._closed = True
        await self._queue.put(None)  # Signal end

    async def events(self) -> AsyncGenerator[Event, None]:
        """Async generator that yields events."""
        while True:
            event = await self._queue.get()
            if event is None:
                break
            yield event

    def is_closed(self) -> bool:
        """Check if emitter is closed."""
        return self._closed
