"""
Flight Agent - Handles flight search and recommendations
"""
from typing import Any, Dict
from .base_agent import BaseAgent
from api.amadeus_client import AmadeusClient


class FlightAgent(BaseAgent):
    """
    Agent responsible for searching and recommending flights
    """

    def __init__(self):
        super().__init__("FlightAgent")
        self.amadeus_client = AmadeusClient()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for flights based on trip requirements

        Args:
            context: Dictionary containing:
                - destination: str
                - origin: str (optional, default to user's location)
                - start_date: datetime
                - end_date: datetime
                - travelers: int
                - budget: float
                - preferences: dict

        Returns:
            Dictionary with flight recommendations
        """
        self.log_info(f"Searching flights to {context.get('destination')}")

        try:
            # TODO: Implement actual flight search using Amadeus API
            flights = await self.amadeus_client.search_flights(
                origin=context.get("origin") or "JFK",
                destination=context.get("destination"),
                departure_date=context["start_date"],
                return_date=context.get("end_date"),
                passengers=context.get("travelers", 1),
            )

            # Filter and rank flights based on preferences and budget
            recommended_flights = self._rank_flights(flights, context)

            return {
                "outbound": recommended_flights.get("outbound", []),
                "return": recommended_flights.get("return", []),
                "total_cost": self._calculate_flight_cost(recommended_flights),
            }

        except Exception as e:
            self.log_error(f"Error searching flights: {str(e)}")
            return {"outbound": [], "return": [], "total_cost": 0.0}

    def _rank_flights(self, flights: list, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rank flights by price (lowest first)"""
        if not flights:
            return {"outbound": [], "return": []}

        sorted_flights = sorted(
            flights,
            key=lambda f: float(f.get("price", {}).get("grandTotal", 999999))
        )

        top_flights = sorted_flights[:10]

        return {
            "outbound": top_flights,
            "return": [],
        }

    def _calculate_flight_cost(self, flights: Dict[str, Any]) -> float:
        """Calculate total flight cost from top ranked flight"""
        outbound = flights.get("outbound", [])
        if outbound:
            return float(outbound[0].get("price", {}).get("grandTotal", 0))
        return 0.0

    async def find_alternatives(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find alternative flights based on current selection

        Args:
            context: Dictionary containing:
                - current_flight_id: str
                - price_range: str (cheaper, same, flexible)
                - flexibility: int (days +/-)
                - destination, dates, etc.

        Returns:
            Dictionary with alternative flights
        """
        self.log_info("Finding alternative flights")

        try:
            # TODO: Implement alternative flight search
            # For now, return simulated alternatives
            return {
                "flights": [
                    {
                        "id": "alt_1",
                        "airline": "Alternative Airline",
                        "price": 500,
                        "duration": "5h 30m",
                        "stops": 0,
                    }
                ]
            }
        except Exception as e:
            self.log_error(f"Error finding alternative flights: {str(e)}")
            return {"flights": []}
