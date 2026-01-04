"""
Travel Agent Orchestrator

ReAct (Reason + Act) loop implementation for the travel planning agent.
Uses Anthropic Claude with tool calling to orchestrate travel planning.
Logs all tool executions and emits structured results for UI rendering.
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
import time
import json
from datetime import datetime

from app.config import settings
from app.agentic.llm import AnthropicLLM, LLMResponse
from app.agentic.tools import BaseTool, get_all_travel_tools
from app.agentic.history import ConversationHistory
from app.agentic.events import EventEmitter, EventType
from app.db import get_tool_execution_service, get_travel_result_service

logger = logging.getLogger(__name__)


# Tool name to result type mapping
TOOL_RESULT_TYPES = {
    "get_weather": "weather",
    "search_flights": "flights",
    "analyze_flight_prices": "flights",
    "search_hotels": "hotels",
    "get_hotel_offers": "hotels",
    "search_transfers": "transfers",
    "search_activities": "activities",
    "convert_currency": "exchange",
    "get_exchange_rates": "exchange",
    "calculate_travel_budget": "exchange",
    "search_flights_api": "flights",
    "create_todo": "todos",
    "create_multiple_todos": "todos",
}


def get_system_prompt() -> str:
    """Generate system prompt with current date."""
    today = datetime.now()
    current_date = today.strftime("%Y-%m-%d")
    current_year = today.year

    return f"""You are AIKU, an intelligent travel planning assistant. Your role is to help users plan their trips by:

1. Understanding their travel needs (destinations, dates, preferences, budget)
2. Searching for flights, hotels, transfers, and activities
3. Providing weather information for destinations
4. Helping with currency conversions and travel budgets
5. Creating comprehensive travel itineraries
6. Creating and managing trip todos/checklists

IMPORTANT - Current Date Information:
- Today's date is: {current_date}
- Current year is: {current_year}
- When users mention dates without a year, assume they mean {current_year}
- For dates that have already passed this year, assume they mean next year ({current_year + 1})
- Always use YYYY-MM-DD format when calling tools (e.g., {current_year}-02-15)

When helping users:
- Ask clarifying questions when details are missing (dates, number of travelers, preferences)
- Use the available tools to search for real-time travel information
- Present options clearly with prices and key details
- Consider the user's budget and preferences when making recommendations
- Be proactive in suggesting relevant services (e.g., transfers, activities)
- ALWAYS search for activities when planning a trip - users want to know what to do at their destination

You have access to these travel services:
- Weather information for any city
- Flight search and price analysis
- Hotel search and booking offers
- Airport transfer search
- Activity and tour search
- Currency conversion and exchange rates
- Travel budget calculation
- Todo/checklist creation for trip planning

CREATING TODOS:
When users ask to create todos, a checklist, packing list, or preparation tasks, use the todo tools:
- Use create_multiple_todos for creating several tasks at once (more efficient)
- Use create_todo for adding a single task
- Categories: packing, booking, documents, activities, transportation, accommodation, other
- Priorities: low, medium, high
- Examples of when to use:
  - "Create a packing list for Paris" -> create multiple todos with packing category
  - "What should I prepare for this trip?" -> suggest and create preparation todos
  - "Add todo to book hotel" -> create single todo with booking category
  - "Make a checklist for the trip" -> create comprehensive trip checklist

Always provide helpful, accurate information and guide users through the travel planning process step by step.

Remember to be friendly, professional, and thorough in your responses. Format your responses clearly using markdown when presenting travel options."""


class TravelAgentOrchestrator:
    """
    Main orchestrator for the travel planning agent.

    Implements the ReAct (Reason + Act) pattern:
    1. Receive user message
    2. Send to Claude with available tools
    3. If Claude wants to use tools, execute them
    4. Log tool executions to database
    5. Emit structured results for UI
    6. Send tool results back to Claude
    7. Repeat until Claude gives final response
    """

    def __init__(
        self,
        llm: Optional[AnthropicLLM] = None,
        tools: Optional[List[BaseTool]] = None,
        max_iterations: int = None,
    ):
        self.llm = llm or AnthropicLLM()
        self.tools = tools or get_all_travel_tools()
        self.max_iterations = max_iterations or settings.LLM_MAX_ITERATIONS

        # Create tool lookup by name
        self._tool_map: Dict[str, BaseTool] = {
            tool.name: tool for tool in self.tools
        }

        # Services
        self._tool_execution_service = get_tool_execution_service()
        self._travel_result_service = get_travel_result_service()

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get OpenAI-style tool schemas for all tools."""
        return [tool.get_schema() for tool in self.tools]

    def _get_result_type(self, tool_name: str) -> Optional[str]:
        """Get the result type for a tool."""
        return TOOL_RESULT_TYPES.get(tool_name)

    async def _emit_structured_result(
        self,
        emitter: EventEmitter,
        tool_name: str,
        result_data: Dict[str, Any],
        parameters: Dict[str, Any],
        tool_execution_id: str,
    ) -> None:
        """Emit structured result for UI rendering based on tool type."""
        result_type = self._get_result_type(tool_name)

        if not result_type or not emitter:
            return

        try:
            if result_type == "weather":
                await emitter.emit_weather(
                    weather=result_data,
                    city=parameters.get("city", "Unknown"),
                    tool_execution_id=tool_execution_id,
                )
            elif result_type == "flights":
                # Extract flights list from result
                flights = result_data.get("flights", [])
                if isinstance(result_data, list):
                    flights = result_data
                await emitter.emit_flights(
                    flights=flights,
                    search_params=parameters,
                    tool_execution_id=tool_execution_id,
                )
            elif result_type == "hotels":
                hotels = result_data.get("hotels", [])
                if isinstance(result_data, list):
                    hotels = result_data
                await emitter.emit_hotels(
                    hotels=hotels,
                    search_params=parameters,
                    tool_execution_id=tool_execution_id,
                )
            elif result_type == "transfers":
                transfers = result_data.get("transfers", [])
                if isinstance(result_data, list):
                    transfers = result_data
                await emitter.emit_transfers(
                    transfers=transfers,
                    search_params=parameters,
                    tool_execution_id=tool_execution_id,
                )
            elif result_type == "activities":
                activities = result_data.get("activities", [])
                if isinstance(result_data, list):
                    activities = result_data
                await emitter.emit_activities(
                    activities=activities,
                    search_params=parameters,
                    tool_execution_id=tool_execution_id,
                )
            elif result_type == "exchange":
                await emitter.emit_exchange(
                    exchange_data=result_data,
                    tool_execution_id=tool_execution_id,
                )
            elif result_type == "todos":
                # Extract todos list from result
                todos = result_data.get("todos", [])
                if result_data.get("todo"):
                    todos = [result_data.get("todo")]
                await emitter.emit_todos(
                    todos=todos,
                    tool_execution_id=tool_execution_id,
                )
        except Exception as e:
            logger.warning(f"Failed to emit structured result for {tool_name}: {e}")

    async def _save_travel_results(
        self,
        conversation_id: str,
        tool_name: str,
        result_data: Dict[str, Any],
        tool_execution_id: str,
    ) -> None:
        """Save travel results to database for later retrieval."""
        result_type = self._get_result_type(tool_name)

        if not result_type:
            return

        try:
            # Map result type to database type
            db_type_map = {
                "weather": "weather",
                "flights": "flight",
                "hotels": "hotel",
                "transfers": "transfer",
                "activities": "activity",
                "exchange": "exchange",
            }
            db_type = db_type_map.get(result_type)

            if not db_type:
                return

            # Handle list results (flights, hotels, etc.)
            if result_type in ["flights", "hotels", "transfers", "activities"]:
                items = result_data.get(result_type, [])
                if isinstance(result_data, list):
                    items = result_data
                if items:
                    await self._travel_result_service.save_results_batch(
                        conversation_id=conversation_id,
                        result_type=db_type,
                        items=items,
                        tool_execution_id=tool_execution_id,
                    )
            else:
                # Single result (weather, exchange)
                await self._travel_result_service.save_result(
                    conversation_id=conversation_id,
                    result_type=db_type,
                    data=result_data,
                    tool_execution_id=tool_execution_id,
                )
        except Exception as e:
            logger.warning(f"Failed to save travel results for {tool_name}: {e}")

    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        conversation_id: str,
        tool_call_id: str,
        emitter: Optional[EventEmitter] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a single tool, log execution, and emit structured result."""
        tool = self._tool_map.get(tool_name)
        start_time = time.time()

        if not tool:
            error_msg = f"Unknown tool: {tool_name}"
            logger.warning(error_msg)

            # Log failed execution
            await self._tool_execution_service.log_execution(
                conversation_id=conversation_id,
                tool_name=tool_name,
                input_params=parameters,
                success=False,
                error_message=error_msg,
                tool_call_id=tool_call_id,
            )

            if emitter:
                await emitter.emit_tool_error(tool_name, error_msg)
            return {"error": error_msg}

        if emitter:
            await emitter.emit_tool_start(tool_name, parameters)

        # Inject context for tools that need it
        exec_params = dict(parameters)
        if getattr(tool, 'needs_context', False):
            exec_params['conversation_id'] = conversation_id
            exec_params['user_id'] = user_id

        try:
            result = await tool.execute(**exec_params)
            duration_ms = int((time.time() - start_time) * 1000)

            if result.success:
                # Log successful execution
                execution = await self._tool_execution_service.log_execution(
                    conversation_id=conversation_id,
                    tool_name=tool_name,
                    input_params=parameters,
                    output_data=result.data,
                    output_type=self._get_result_type(tool_name),
                    success=True,
                    duration_ms=duration_ms,
                    tool_call_id=tool_call_id,
                )

                execution_id = execution.get("id", "")

                # Emit structured result for UI
                if emitter:
                    await self._emit_structured_result(
                        emitter=emitter,
                        tool_name=tool_name,
                        result_data=result.data,
                        parameters=parameters,
                        tool_execution_id=execution_id,
                    )
                    await emitter.emit_tool_end(tool_name, result.data, success=True)

                # Save travel results to database
                await self._save_travel_results(
                    conversation_id=conversation_id,
                    tool_name=tool_name,
                    result_data=result.data,
                    tool_execution_id=execution_id,
                )

                return result.data
            else:
                # Log failed execution
                await self._tool_execution_service.log_execution(
                    conversation_id=conversation_id,
                    tool_name=tool_name,
                    input_params=parameters,
                    success=False,
                    error_message=result.error,
                    duration_ms=duration_ms,
                    tool_call_id=tool_call_id,
                )

                if emitter:
                    await emitter.emit_tool_end(tool_name, result.error, success=False)
                return {"error": result.error}

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            duration_ms = int((time.time() - start_time) * 1000)
            logger.exception(f"Error executing tool {tool_name}")

            # Log exception
            await self._tool_execution_service.log_execution(
                conversation_id=conversation_id,
                tool_name=tool_name,
                input_params=parameters,
                success=False,
                error_message=error_msg,
                duration_ms=duration_ms,
                tool_call_id=tool_call_id,
            )

            if emitter:
                await emitter.emit_tool_error(tool_name, error_msg)
            return {"error": error_msg}

    async def _execute_tools(
        self,
        tool_calls: List[Dict[str, Any]],
        conversation_id: str,
        emitter: Optional[EventEmitter] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute multiple tool calls and return results."""
        results = []

        for tool_call in tool_calls:
            tool_id = tool_call.get("id", "")
            tool_name = tool_call.get("function", {}).get("name", "")
            parameters = tool_call.get("function", {}).get("arguments", {})

            # Parse parameters if string
            if isinstance(parameters, str):
                try:
                    parameters = json.loads(parameters)
                except json.JSONDecodeError:
                    parameters = {}

            result = await self._execute_tool(
                tool_name=tool_name,
                parameters=parameters,
                conversation_id=conversation_id,
                tool_call_id=tool_id,
                emitter=emitter,
                user_id=user_id,
            )

            # Convert result to string for conversation history
            if isinstance(result, dict):
                result_str = json.dumps(result, ensure_ascii=False)
            else:
                result_str = str(result)

            results.append({
                "tool_call_id": tool_id,
                "content": result_str,
            })

        return results

    async def run(
        self,
        user_message: str,
        conversation: ConversationHistory,
        emitter: Optional[EventEmitter] = None,
    ) -> str:
        """
        Run the ReAct loop for a user message.

        Args:
            user_message: The user's message
            conversation: Conversation history
            emitter: Optional event emitter for SSE streaming

        Returns:
            The final assistant response
        """
        conversation_id = conversation.conversation_id
        user_id = conversation.user_id

        # Add user message to history
        conversation.add_user_message(user_message)

        if emitter:
            await emitter.emit_thinking("Understanding your request...")

        iteration = 0
        final_response = ""

        while iteration < self.max_iterations:
            iteration += 1

            if emitter:
                await emitter.emit_iteration(iteration, self.max_iterations)

            # Get LLM response
            try:
                llm_response = await self.llm.chat(
                    messages=conversation.get_messages_for_llm(),
                    system=get_system_prompt(),
                    tools=self.get_tool_schemas(),
                )
            except Exception as e:
                error_msg = f"LLM error: {str(e)}"
                logger.exception("LLM call failed")
                if emitter:
                    await emitter.emit_error(error_msg)
                raise

            # Check if we have tool calls
            if llm_response.tool_calls:
                if emitter:
                    await emitter.emit_thinking(f"Using {len(llm_response.tool_calls)} tool(s)...")

                # Add assistant message with tool calls
                conversation.add_assistant_message(
                    content=llm_response.content or "",
                    tool_calls=[tc.to_dict() for tc in llm_response.tool_calls],
                )

                # Execute tools (with logging and structured result emission)
                tool_results = await self._execute_tools(
                    tool_calls=[tc.to_dict() for tc in llm_response.tool_calls],
                    conversation_id=conversation_id,
                    emitter=emitter,
                    user_id=user_id,
                )

                # Add tool results to conversation
                for result in tool_results:
                    conversation.add_tool_result(
                        tool_call_id=result["tool_call_id"],
                        content=result["content"],
                    )

                # Continue loop to get next response
                continue

            # No tool calls - this is the final response
            final_response = llm_response.content or ""
            conversation.add_assistant_message(content=final_response)

            if emitter:
                await emitter.emit_message(final_response)
                await emitter.emit_complete()

            break

        # Safety check for max iterations
        if iteration >= self.max_iterations and not final_response:
            final_response = "I apologize, but I reached the maximum number of steps while processing your request. Please try simplifying your question."
            conversation.add_assistant_message(content=final_response)

            if emitter:
                await emitter.emit_message(final_response)
                await emitter.emit_complete()

        return final_response

    async def run_stream(
        self,
        user_message: str,
        conversation: ConversationHistory,
    ) -> AsyncGenerator[str, None]:
        """
        Run the ReAct loop with SSE streaming.

        Yields SSE-formatted events including:
        - thinking: Agent is processing
        - tool_start: Starting tool execution
        - tool_end: Tool execution complete
        - flights/hotels/weather/etc: Structured results for UI
        - message: Final response text
        - complete: Stream complete
        """
        emitter = EventEmitter()

        # Start orchestration in background
        import asyncio

        async def run_orchestration():
            try:
                await self.run(user_message, conversation, emitter)
            except Exception as e:
                await emitter.emit_error(str(e))

        task = asyncio.create_task(run_orchestration())

        # Yield events as they come
        async for event in emitter.events():
            yield event.to_sse()

        # Ensure task is complete
        await task


# Singleton instance for convenience
_orchestrator: Optional[TravelAgentOrchestrator] = None


def get_orchestrator() -> TravelAgentOrchestrator:
    """Get the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TravelAgentOrchestrator()
    return _orchestrator
