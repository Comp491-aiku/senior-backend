"""
Hotel Tools

Search hotels and get room offers.
"""

from typing import Any, Dict, Optional

from app.agentic.tools.http_tool import HttpTool
from app.agentic.tools.types import ToolResult
from app.config import settings


class SearchHotelsTool(HttpTool):
    """
    Search for hotels in a city.

    Returns hotel list with names, ratings, locations, and amenities.
    """

    def __init__(self):
        super().__init__(base_url=settings.HOTEL_AGENT_URL, timeout=30.0)

    @property
    def name(self) -> str:
        return "search_hotels"

    @property
    def description(self) -> str:
        return (
            "**REQUIRED for hotel queries** Search for hotels in a city with optional star rating filter. "
            "Returns hotel list with names, ratings, locations, amenities, "
            "and distance from center. ALWAYS use this tool when users ask about hotels, "
            "accommodation, or where to stay in a destination."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "city_code": {
                    "type": "string",
                    "description": "IATA city code (e.g., 'PAR' for Paris, 'LON' for London, 'IST' for Istanbul)"
                },
                "check_in_date": {
                    "type": "string",
                    "description": "Check-in date in YYYY-MM-DD format"
                },
                "check_out_date": {
                    "type": "string",
                    "description": "Check-out date in YYYY-MM-DD format"
                },
                "adults": {
                    "type": "integer",
                    "description": "Number of adult guests (default: 2)"
                },
                "rooms": {
                    "type": "integer",
                    "description": "Number of rooms needed (default: 1)"
                },
                "ratings": {
                    "type": "string",
                    "description": "Star ratings to filter, comma-separated (e.g., '4,5' for 4 and 5 star hotels)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of hotels to return (default: 15)"
                }
            },
            "required": ["city_code", "check_in_date", "check_out_date"]
        }

    async def execute(
        self,
        city_code: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 2,
        rooms: int = 1,
        ratings: Optional[str] = None,
        limit: int = 15,
        **kwargs,
    ) -> ToolResult:
        """Execute hotel search request."""
        # Cap limit to prevent token overflow
        limit = min(limit, 20)
        
        return await self.get(
            "/api/hotels",
            params={
                "city_code": city_code,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "adults": adults,
                "rooms": rooms,
                "ratings": ratings,
                "max": limit,
            }
        )


class GetHotelOffersTool(HttpTool):
    """
    Get hotel room offers with prices.

    Returns available rooms, prices, cancellation policies, and meal options.
    """

    def __init__(self):
        super().__init__(base_url=settings.HOTEL_AGENT_URL, timeout=60.0)

    @property
    def name(self) -> str:
        return "get_hotel_offers"

    @property
    def description(self) -> str:
        return (
            "**REQUIRED for hotel pricing** Get hotel room offers with prices for specific dates. "
            "Returns available rooms, prices per night, total prices, cancellation policies, "
            "and meal options (breakfast, half-board, etc.). ALWAYS use this when users ask "
            "about hotel prices, room rates, or want detailed booking information."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "city_code": {
                    "type": "string",
                    "description": "IATA city code - use this OR hotel_ids"
                },
                "hotel_ids": {
                    "type": "string",
                    "description": "Comma-separated hotel IDs - use this OR city_code"
                },
                "check_in_date": {
                    "type": "string",
                    "description": "Check-in date in YYYY-MM-DD format"
                },
                "check_out_date": {
                    "type": "string",
                    "description": "Check-out date in YYYY-MM-DD format"
                },
                "adults": {
                    "type": "integer",
                    "description": "Number of adult guests (default: 2)"
                },
                "rooms": {
                    "type": "integer",
                    "description": "Number of rooms needed (default: 1)"
                },
                "currency": {
                    "type": "string",
                    "description": "Currency for prices (default: USD)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of hotel offers to return (default: 10)"
                }
            },
            "required": ["check_in_date", "check_out_date"]
        }

    async def execute(
        self,
        check_in_date: str,
        check_out_date: str,
        city_code: Optional[str] = None,
        hotel_ids: Optional[str] = None,
        adults: int = 2,
        rooms: int = 1,
        currency: str = "USD",
        limit: int = 10,
        **kwargs,
    ) -> ToolResult:
        """Execute hotel offers request."""
        # Cap limit to prevent token overflow
        limit = min(limit, 15)
        
        # Hotels endpoint returns both hotel info and offers
        return await self.get(
            "/api/hotels",
            params={
                "city_code": city_code,
                "hotel_ids": hotel_ids,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "adults": adults,
                "rooms": rooms,
                "currency": currency,
                "max": limit,
            }
        )
