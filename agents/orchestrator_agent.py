"""
Orchestrator Agent - Coordinates all other agents
"""
from typing import Any, Dict
from .base_agent import BaseAgent
from .flight_agent import FlightAgent
from .accommodation_agent import AccommodationAgent
from .activity_agent import ActivityAgent
from .weather_agent import WeatherAgent


class OrchestratorAgent(BaseAgent):
    """
    Main orchestrator that coordinates all specialized agents
    to create a complete travel itinerary
    """

    def __init__(self):
        super().__init__("OrchestratorAgent")
        self.flight_agent = FlightAgent()
        self.accommodation_agent = AccommodationAgent()
        self.activity_agent = ActivityAgent()
        self.weather_agent = WeatherAgent()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate the complete itinerary generation process

        Args:
            context: Dictionary containing trip details:
                - destination: str
                - start_date: datetime
                - end_date: datetime
                - budget: float
                - travelers: int
                - preferences: dict

        Returns:
            Complete itinerary with flights, accommodations, activities, and weather
        """
        self.log_info("Starting itinerary generation orchestration")

        try:
            # Step 1: Get weather forecast
            self.log_info("Fetching weather forecast")
            weather_data = await self.weather_agent.execute(context)

            # Step 2: Search for flights
            self.log_info("Searching for flights")
            flight_data = await self.flight_agent.execute(context)

            # Step 3: Search for accommodations
            self.log_info("Searching for accommodations")
            accommodation_data = await self.accommodation_agent.execute(context)

            # Step 4: Plan activities
            self.log_info("Planning activities")
            activity_context = {
                **context,
                "weather": weather_data,
            }
            activity_data = await self.activity_agent.execute(activity_context)

            # Step 5: Combine all data into a complete itinerary
            itinerary = self._build_itinerary(
                context=context,
                flights=flight_data,
                accommodations=accommodation_data,
                activities=activity_data,
                weather=weather_data,
            )

            self.log_info("Itinerary generation completed successfully")
            return itinerary

        except Exception as e:
            self.log_error(f"Error during orchestration: {str(e)}")
            raise

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
