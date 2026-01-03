"""
Flight Tools

Search flights and analyze prices.
"""

from typing import Any, Dict, Optional

from app.agentic.tools.http_tool import HttpTool
from app.agentic.tools.types import ToolResult
from app.config import settings


class SearchFlightsTool(HttpTool):
    """
    Search for flights between airports.

    Returns flight options with prices, schedules, airlines,
    duration, and number of stops.
    """

    def __init__(self):
        super().__init__(base_url=settings.FLIGHT_AGENT_URL, timeout=60.0)

    @property
    def name(self) -> str:
        return "search_flights"

    @property
    def description(self) -> str:
        return (
            "Search for flights between two airports. Returns flight options with prices, "
            "schedules, airlines, duration, and number of stops. Can search one-way or "
            "round-trip flights. Use this when users want to find and compare flight options."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "Departure airport IATA code (e.g., 'IST', 'JFK', 'CDG')"
                },
                "destination": {
                    "type": "string",
                    "description": "Arrival airport IATA code (e.g., 'CDG', 'LHR', 'BCN')"
                },
                "departure_date": {
                    "type": "string",
                    "description": "Departure date in YYYY-MM-DD format"
                },
                "return_date": {
                    "type": "string",
                    "description": "Return date in YYYY-MM-DD format (optional, for round-trip)"
                },
                "adults": {
                    "type": "integer",
                    "description": "Number of adult passengers (default: 1)"
                },
                "children": {
                    "type": "integer",
                    "description": "Number of children (default: 0)"
                },
                "cabin": {
                    "type": "string",
                    "enum": ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
                    "description": "Cabin class (default: ECONOMY)"
                },
                "nonstop": {
                    "type": "boolean",
                    "description": "Only show direct flights (default: false)"
                },
                "currency": {
                    "type": "string",
                    "description": "Currency for prices (default: USD)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 10)"
                }
            },
            "required": ["origin", "destination", "departure_date"]
        }

    async def execute(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        cabin: str = "ECONOMY",
        nonstop: bool = False,
        currency: str = "USD",
        limit: int = 10,
        **kwargs,
    ) -> ToolResult:
        """Execute flight search request."""
        return await self.get(
            "/api/flights",
            params={
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "adults": adults,
                "children": children,
                "cabin": cabin,
                "nonstop": nonstop,
                "currency": currency,
                "max": limit,
            }
        )


class AnalyzeFlightPricesTool(HttpTool):
    """
    Analyze flight prices and get recommendations.

    Returns price statistics and suggested dates with potential savings.
    """

    def __init__(self):
        super().__init__(base_url=settings.FLIGHT_AGENT_URL, timeout=60.0)

    @property
    def name(self) -> str:
        return "analyze_flight_prices"

    @property
    def description(self) -> str:
        return (
            "Analyze flight prices for a route and get recommendations for the best "
            "dates to fly. Returns price statistics (min, max, avg) and suggested dates "
            "with potential savings percentage. Use this to help users find the cheapest days to travel."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "Departure airport IATA code"
                },
                "destination": {
                    "type": "string",
                    "description": "Arrival airport IATA code"
                },
                "departure_date": {
                    "type": "string",
                    "description": "Reference date in YYYY-MM-DD format"
                }
            },
            "required": ["origin", "destination", "departure_date"]
        }

    async def execute(
        self, origin: str, destination: str, departure_date: str, **kwargs
    ) -> ToolResult:
        """Execute price analysis request."""
        return await self.get(
            "/api/flights/price-analysis",
            params={
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
            }
        )
