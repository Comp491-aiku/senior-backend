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
            "Search for hotels in a city with optional star rating filter. "
            "Returns hotel list with names, ratings, locations, amenities, "
            "and distance from center. Use this to find available hotels in a destination."
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
        **kwargs,
    ) -> ToolResult:
        """Execute hotel search request."""
        return await self.get(
            "/api/hotels",
            params={
                "city_code": city_code,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "adults": adults,
                "rooms": rooms,
                "ratings": ratings,
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
            "Get hotel room offers with prices for specific dates. Returns available rooms, "
            "prices per night, total prices, cancellation policies, and meal options "
            "(breakfast, half-board, etc.). Use this when users have selected dates "
            "and want to see actual room prices."
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
        **kwargs,
    ) -> ToolResult:
        """Execute hotel offers request."""
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
            }
        )
