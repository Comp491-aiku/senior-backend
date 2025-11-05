"""
Orchestrator Agent - Coordinates all other agents with intelligent execution strategy
"""
from typing import Any, Dict, AsyncGenerator
import asyncio
from anthropic import Anthropic
from utils.config import settings
from .base_agent import BaseAgent
from .flight_agent import FlightAgent
from .accommodation_agent import AccommodationAgent
from .activity_agent import ActivityAgent
from .weather_agent import WeatherAgent


class OrchestratorAgent(BaseAgent):
    """
    Main orchestrator that coordinates all specialized agents
    to create a complete travel itinerary.

    Features:
    - Intelligent parallel vs sequential execution decisions
    - Natural language understanding
    - Real-time streaming of agent activity
    - Support for different planning modes (plan, auto-pay, edit)
    """

    def __init__(self):
        super().__init__("OrchestratorAgent")
        self.flight_agent = FlightAgent()
        self.accommodation_agent = AccommodationAgent()
        self.activity_agent = ActivityAgent()
        self.weather_agent = WeatherAgent()
        self.ai_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate the complete itinerary generation process

        Args:
            context: Dictionary containing:
                - message: Natural language user input
                - planning_mode: 'plan', 'auto-pay', or 'edit'
                - trip_id: Optional existing trip ID
                - user_id: User ID
                - chat_history: Previous conversation

        Returns:
            Complete response with agent activity and AI response
        """
        self.log_info("Starting orchestration")

        try:
            # Parse user intent from natural language
            intent = await self._parse_user_intent(context)

            # Decide execution strategy (parallel vs sequential)
            execution_plan = self._create_execution_plan(intent)

            # Execute agents based on plan
            agent_results = await self._execute_agents(execution_plan, context)

            # Generate AI response
            ai_response = await self._generate_response(intent, agent_results, context)

            # Build final result
            result = {
                "response": ai_response,
                "agent_activity": execution_plan.get("agent_activity", []),
                "trip_id": context.get("trip_id"),
                "intent": intent,
                **agent_results
            }

            self.log_info("Orchestration completed successfully")
            return result

        except Exception as e:
            self.log_error(f"Error during orchestration: {str(e)}")
            return {
                "response": "I encountered an error while processing your request. Please try again.",
                "agent_activity": [{
                    "agent": "Orchestrator",
                    "status": "failed",
                    "message": f"Error: {str(e)}"
                }],
                "error": str(e)
            }

    async def stream_execution(self, context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream agent execution in real-time for SSE

        Yields:
            Agent activity updates as they happen
        """
        try:
            # Yield initial orchestrator activity
            yield {
                "agent": "Orchestrator",
                "status": "running",
                "message": "Analyzing your request...",
                "progress": 10
            }

            # Parse user intent
            intent = await self._parse_user_intent(context)

            yield {
                "agent": "Orchestrator",
                "status": "completed",
                "message": f"Understood: {intent.get('summary', 'Planning your trip')}",
                "progress": 20
            }

            # Create execution plan
            execution_plan = self._create_execution_plan(intent)

            # Execute agents and stream their activity
            async for activity in self._execute_agents_streaming(execution_plan, context):
                yield activity

            # Generate final response
            yield {
                "agent": "Orchestrator",
                "status": "completed",
                "message": "Trip plan ready!",
                "progress": 100
            }

        except Exception as e:
            yield {
                "agent": "Orchestrator",
                "status": "failed",
                "message": f"Error: {str(e)}"
            }

    async def _parse_user_intent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse natural language user input to understand intent

        Returns:
            Intent dictionary with destination, dates, preferences, etc.
        """
        user_message = context.get("message", "")

        # If AI client is available, use Claude to parse intent
        if self.ai_client:
            try:
                prompt = f"""Parse this travel planning request and extract structured information:

User message: "{user_message}"

Extract and return JSON with:
- destination: Where they want to go
- duration: How many days (if mentioned)
- budget: Budget amount and currency (if mentioned)
- travelers: Number of people (if mentioned)
- preferences: List of preferences (luxury, budget, adventure, etc.)
- action: What they want to do (plan_trip, find_alternative, edit_trip, etc.)
- summary: One sentence summary of their request

Return only valid JSON, no other text."""

                # Note: This is a simplified version. In production, use proper Claude API call
                # For now, return a simple parsed intent
                pass
            except Exception as e:
                self.log_error(f"Error parsing intent with AI: {str(e)}")

        # Fallback: Simple keyword-based parsing
        return self._simple_parse_intent(user_message, context)

    def _simple_parse_intent(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simple keyword-based intent parsing"""
        message_lower = message.lower()

        intent = {
            "action": "plan_trip",  # default action
            "summary": message[:100],
            "needs_flights": "flight" in message_lower or "fly" in message_lower,
            "needs_accommodation": "hotel" in message_lower or "stay" in message_lower or "accommodation" in message_lower,
            "needs_activities": "activity" in message_lower or "things to do" in message_lower or "visit" in message_lower,
            "planning_mode": context.get("planning_mode", "plan")
        }

        # Check for alternative finding
        if any(word in message_lower for word in ["alternative", "different", "other", "cheaper", "better"]):
            intent["action"] = "find_alternative"

        # Check for editing
        elif any(word in message_lower for word in ["edit", "change", "modify", "update"]):
            intent["action"] = "edit_trip"

        return intent

    def _create_execution_plan(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create execution plan deciding parallel vs sequential execution

        Returns:
            Execution plan with agent sequence and parallelization strategy
        """
        plan = {
            "agents": [],
            "parallel_groups": [],
            "agent_activity": []
        }

        action = intent.get("action", "plan_trip")

        if action == "plan_trip":
            # Weather can run independently first
            plan["agents"].append({"agent": "weather", "dependencies": []})

            # Flights and accommodations can run in parallel after weather
            # But activities depend on weather data
            if intent.get("needs_flights") or intent.get("needs_accommodation"):
                plan["parallel_groups"].append({
                    "agents": ["flight", "accommodation"] if intent.get("needs_flights") and intent.get("needs_accommodation")
                             else ["flight"] if intent.get("needs_flights")
                             else ["accommodation"],
                    "dependencies": ["weather"]
                })

            # Activities run after we know weather
            if intent.get("needs_activities"):
                plan["agents"].append({"agent": "activity", "dependencies": ["weather"]})

        elif action == "find_alternative":
            # Finding alternatives is usually a single focused task
            plan["agents"].append({"agent": "determine_from_intent", "dependencies": []})

        return plan

    async def _execute_agents(self, execution_plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents based on execution plan"""
        results = {}

        # For now, execute a simple version
        # In production, implement full parallel/sequential execution based on plan

        return results

    async def _execute_agents_streaming(self, execution_plan: Dict[str, Any], context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute agents and stream their activity"""

        # Simulate agent execution with streaming
        agents_to_run = ["Flight Agent", "Accommodation Agent", "Activity Agent", "Weather Agent"]

        for i, agent_name in enumerate(agents_to_run):
            yield {
                "agent": agent_name,
                "status": "running",
                "message": f"Searching for best options...",
                "progress": 30 + (i * 15)
            }

            # Simulate work
            await asyncio.sleep(0.5)

            yield {
                "agent": agent_name,
                "status": "completed",
                "message": f"Found options for {agent_name.lower().replace(' agent', '')}",
                "progress": 30 + ((i + 1) * 15)
            }

    async def _generate_response(self, intent: Dict[str, Any], agent_results: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate natural language response based on agent results"""

        # Simple response for now
        mode = context.get("planning_mode", "plan")

        if mode == "plan":
            return "I've found some great options for your trip! I've searched for flights, accommodations, and activities based on your preferences. Would you like to see the details or make any changes?"
        elif mode == "auto-pay":
            return "I've found the best options and I'm ready to book them automatically if you approve. Here's what I found..."
        else:  # edit mode
            return "I've found alternative options based on your request. Here are some different choices you might like..."

    def _build_itinerary(
        self,
        context: Dict[str, Any],
        flights: Dict[str, Any],
        accommodations: Dict[str, Any],
        activities: Dict[str, Any],
        weather: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build the final itinerary from all agent outputs
        """
        # TODO: Implement smart scheduling and optimization
        return {
            "destination": context["destination"],
            "dates": {
                "start": context["start_date"],
                "end": context["end_date"],
            },
            "flights": flights,
            "accommodations": accommodations,
            "activities": activities,
            "weather": weather,
            "total_cost": self._calculate_total_cost(flights, accommodations, activities),
        }

    def _calculate_total_cost(
        self, flights: Dict, accommodations: Dict, activities: Dict
    ) -> float:
        """Calculate the total cost of the trip"""
        total = 0.0
        # TODO: Implement actual cost calculation
        return total
