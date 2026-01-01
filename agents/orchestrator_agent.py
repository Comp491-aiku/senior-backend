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

            # Enrich context with parsed intent for agents
            enriched_context = self._enrich_context(context, intent)

            # Decide execution strategy (parallel vs sequential)
            execution_plan = self._create_execution_plan(intent)

            # Execute agents based on plan
            agent_results = await self._execute_agents(execution_plan, enriched_context)

            # Build structured itinerary from agent results
            itinerary = self._build_itinerary(
                context=enriched_context,
                flights=agent_results.get("flight", {}),
                accommodations=agent_results.get("accommodation", {}),
                activities=agent_results.get("activity", {}),
                weather=agent_results.get("weather", {}),
            )

            # Generate AI response
            ai_response = await self._generate_response(intent, agent_results, enriched_context)

            # Build final result
            result = {
                "response": ai_response,
                "itinerary": itinerary,
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
        import json

        user_message = context.get("message", "")
        # TODO: Remove after flow is working and we can test using claude to extract intent
        return self._simple_parse_intent(user_message, context)
        # If AI client is available, use Claude to parse intent
        if not self.ai_client:
            self.log_info("Claude AI client not configured, using fallback parser")

        if self.ai_client:
            try:
                prompt = f"""Parse this travel planning request and extract structured information.

User message: "{user_message}"

Extract and return a JSON object with these fields:
- destination: The city or place they want to visit (string, required)
- origin: Where they're traveling from if mentioned (string or null)
- duration: Number of days for the trip (integer or null)
- budget: Budget amount in USD (number or null)
- travelers: Number of people traveling (integer, default 1)
- preferences: List of travel preferences like ["luxury", "adventure", "budget-friendly", "family-friendly"] (array)
- action: One of "plan_trip", "find_alternative", or "edit_trip"
- needs_flights: Whether they need flight booking (boolean)
- needs_accommodation: Whether they need hotel/accommodation (boolean)
- needs_activities: Whether they want activity recommendations (boolean)
- summary: Brief one-sentence summary of their request

Return ONLY valid JSON, no markdown, no explanation."""

                response = self.ai_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                response_text = response.content[0].text.strip()

                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.strip()

                intent = json.loads(response_text)
                intent["planning_mode"] = context.get("planning_mode", "plan")

                self.log_info(f"Parsed intent with Claude: {intent.get('summary', 'No summary')}")
                return intent

            except json.JSONDecodeError as e:
                self.log_error(f"Failed to parse Claude response as JSON: {str(e)}")
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
            "needs_flights": True,  # Default to True for trip planning
            "needs_accommodation": True,  # Default to True for trip planning
            "needs_activities": True,  # Default to True for trip planning
            "planning_mode": context.get("planning_mode", "plan")
        }

        # Extract destination (look for "to <city>" pattern)
        import re
        destination_match = re.search(r'\bto\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)', message)
        if destination_match:
            intent["destination"] = destination_match.group(1)

        # Extract number of days
        days_match = re.search(r'(\d+)\s*(?:days?|nights?)', message_lower)
        if days_match:
            intent["duration"] = int(days_match.group(1))

        # Extract number of travelers
        travelers_match = re.search(r'(\d+)\s*(?:people|persons?|travelers?|guests?)', message_lower)
        if travelers_match:
            intent["travelers"] = int(travelers_match.group(1))

        # Extract budget
        budget_match = re.search(r'\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:budget|dollars?|usd)?', message_lower)
        if budget_match:
            intent["budget"] = float(budget_match.group(1).replace(',', ''))

        # Check for alternative finding
        if any(word in message_lower for word in ["alternative", "different", "other", "cheaper", "better"]):
            intent["action"] = "find_alternative"

        # Check for editing
        elif any(word in message_lower for word in ["edit", "change", "modify", "update"]):
            intent["action"] = "edit_trip"

        return intent

    def _enrich_context(self, context: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich context with parsed intent values for agents"""
        from datetime import datetime, timedelta

        enriched = context.copy()

        enriched["destination"] = intent.get("destination")

        # Add dates (default to next week if not specified)
        if "start_date" not in enriched:
            enriched["start_date"] = datetime.now()
        if "end_date" not in enriched:
            duration = intent.get("duration") or 5
            enriched["end_date"] = enriched["start_date"] + timedelta(days=duration)

        enriched["travelers"] = intent.get("travelers") or context.get("travelers") or 1
        enriched["budget"] = intent.get("budget") or context.get("budget") or 2000
        enriched["preferences"] = context.get("preferences") or {}
        enriched["origin"] = intent.get("origin") or context.get("origin") or "JFK"

        return enriched

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
        results = {}
        completed = set()

        agent_map = {
            "weather": self.weather_agent,
            "flight": self.flight_agent,
            "accommodation": self.accommodation_agent,
            "activity": self.activity_agent,
        }

        all_agents = []
        for agent_entry in execution_plan.get("agents", []):
            all_agents.append({
                "name": agent_entry["agent"],
                "dependencies": agent_entry.get("dependencies", []),
                "parallel": False
            })

        for group in execution_plan.get("parallel_groups", []):
            for agent_name in group.get("agents", []):
                all_agents.append({
                    "name": agent_name,
                    "dependencies": group.get("dependencies", []),
                    "parallel": True,
                    "group_agents": group.get("agents", [])
                })

        pending = list(all_agents)
        while pending:
            ready = [a for a in pending if all(dep in completed for dep in a["dependencies"])]

            if not ready:
                self.log_error("Circular dependency or missing agent detected")
                break

            parallel_batch = []
            sequential = []
            processed_groups = set()

            for agent in ready:
                if agent["parallel"]:
                    group_key = tuple(sorted(agent.get("group_agents", [])))
                    if group_key not in processed_groups:
                        parallel_batch.extend([a for a in ready if a.get("group_agents") and tuple(sorted(a["group_agents"])) == group_key])
                        processed_groups.add(group_key)
                else:
                    sequential.append(agent)

            for agent_entry in sequential:
                agent_name = agent_entry["name"]
                if agent_name in agent_map:
                    self.log_info(f"Executing {agent_name} agent")
                    try:
                        results[agent_name] = await agent_map[agent_name].execute(context)
                    except Exception as e:
                        self.log_error(f"Error executing {agent_name}: {str(e)}")
                        results[agent_name] = {"error": str(e)}
                    completed.add(agent_name)
                pending = [a for a in pending if a["name"] != agent_name]

            if parallel_batch:
                unique_agents = {a["name"]: a for a in parallel_batch}
                tasks = []
                agent_names = []

                for agent_name in unique_agents:
                    if agent_name in agent_map:
                        self.log_info(f"Executing {agent_name} agent (parallel)")
                        tasks.append(agent_map[agent_name].execute(context))
                        agent_names.append(agent_name)

                if tasks:
                    try:
                        task_results = await asyncio.gather(*tasks, return_exceptions=True)
                        for name, result in zip(agent_names, task_results):
                            if isinstance(result, Exception):
                                self.log_error(f"Error executing {name}: {str(result)}")
                                results[name] = {"error": str(result)}
                            else:
                                results[name] = result
                            completed.add(name)
                    except Exception as e:
                        self.log_error(f"Error in parallel execution: {str(e)}")

                pending = [a for a in pending if a["name"] not in unique_agents]

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

        '''
        mode = context.get("planning_mode", "plan")

        if mode == "plan":
            return "I've found some great options for your trip! I've searched for flights, accommodations, and activities based on your preferences. Would you like to see the details or make any changes?"
        elif mode == "auto-pay":
            return "I've found the best options and I'm ready to book them automatically if you approve. Here's what I found..."
        else:  # edit mode
            return "I've found alternative options based on your request. Here are some different choices you might like..."
        '''

        destination = context.get("destination", "your destination")
        parts = []

        # Flight summary
        flight_data = agent_results.get("flight", {})
        outbound_flights = flight_data.get("outbound", [])
        if outbound_flights:
            best_flight = outbound_flights[0]
            price = best_flight.get("price", {})
            total = price.get("grandTotal", "N/A")
            currency = price.get("currency", "USD")
            parts.append(f"Found {len(outbound_flights)} flight options. Best price: {currency} {total}")
        else:
            parts.append("No flights found for your dates")

        # Accommodation summary
        accommodation_data = agent_results.get("accommodation", {})
        hotel_option = accommodation_data.get("options")
        if hotel_option:
            hotel_name = hotel_option.hotel.name if hasattr(hotel_option, 'hotel') else "Hotel"
            if hasattr(hotel_option, 'offers') and hotel_option.offers:
                offer = hotel_option.offers[0]
                hotel_total = offer.price.total
                hotel_currency = offer.price.currency
                parts.append(f"Top hotel: {hotel_name} at {hotel_currency} {hotel_total}")
            else:
                parts.append(f"Top hotel: {hotel_name}")
        else:
            parts.append("No accommodations found for your dates")

        # Weather summary
        weather_data = agent_results.get("weather", {})
        forecasts = weather_data.get("daily_forecast", [])
        if forecasts:
            avg_temps = [f.temperature.avg or f.temperature.max for f in forecasts if hasattr(f, 'temperature')]
            avg_temp = sum(avg_temps) / len(avg_temps) if avg_temps else 0
            unit = forecasts[0].temperature.unit[0].upper() if hasattr(forecasts[0], 'temperature') else "C"
            parts.append(f"Weather forecast: Average {avg_temp:.0f}°{unit}")

        # Activity summary
        activity_data = agent_results.get("activity", {})
        total_activities = activity_data.get("total_activities", 0)
        if total_activities > 0:
            parts.append(f"Found {total_activities} activities and attractions")

        summary = f"Here's what I found for your trip to {destination}:\n\n"
        summary += "\n".join(f"• {part}\n" for part in parts)
        summary += "\n\nWould you like to see the details or make any changes?"

        return summary

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
        #TODO: need to update for models
        total = 0.0

        # Flight cost
        flight_cost = flights.get("total_cost", 0)
        if flight_cost:
            total += float(flight_cost)

        # Accommodation cost
        accom_cost = accommodations.get("total_cost", 0)
        if accom_cost:
            total += float(accom_cost)

        # Activity cost
        activity_cost = activities.get("estimated_cost", 0)
        if activity_cost:
            total += float(activity_cost)

        return total
