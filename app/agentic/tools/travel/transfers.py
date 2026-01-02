"""
Transfer Tool

Search for airport transfer options.
"""

from typing import Any, Dict, Optional

from app.agentic.tools.http_tool import HttpTool
from app.agentic.tools.types import ToolResult
from app.config import settings


class SearchTransfersTool(HttpTool):
    """
    Search for airport transfer options.

    Returns available vehicles, prices, duration, and cancellation policies.
    """

    def __init__(self):
        super().__init__(base_url=settings.TRANSFER_AGENT_URL, timeout=30.0)

    @property
    def name(self) -> str:
        return "search_transfers"

    @property
    def description(self) -> str:
        return (
            "Search for airport transfer options (private car, shared shuttle, taxi, airport bus). "
            "Returns available vehicles, prices, duration, capacity, and cancellation policies. "
            "Use this to help users get from airport to hotel or specific locations."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "from": {
                    "type": "string",
                    "description": "Departure airport IATA code (e.g., 'CDG', 'IST', 'LHR')"
                },
                "to_lat": {
                    "type": "number",
                    "description": "Destination latitude - use this with to_lng OR use to_address"
                },
                "to_lng": {
                    "type": "number",
                    "description": "Destination longitude - use this with to_lat OR use to_address"
                },
                "to_address": {
                    "type": "string",
                    "description": "Destination address (alternative to coordinates)"
                },
                "to_city": {
                    "type": "string",
                    "description": "Destination city (use with to_address)"
                },
                "date_time": {
                    "type": "string",
                    "description": "Transfer date and time in ISO 8601 format (e.g., '2026-02-15T14:00:00')"
                },
                "passengers": {
                    "type": "integer",
                    "description": "Number of passengers"
                },
                "type": {
                    "type": "string",
                    "enum": ["PRIVATE", "SHARED", "TAXI", "HOURLY", "AIRPORT_EXPRESS", "AIRPORT_BUS"],
                    "description": "Transfer type filter (optional)"
                }
            },
            "required": ["from", "date_time", "passengers"]
        }

    async def execute(
        self,
        date_time: str,
        passengers: int,
        to_lat: Optional[float] = None,
        to_lng: Optional[float] = None,
        to_address: Optional[str] = None,
        to_city: Optional[str] = None,
        type: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """Execute transfer search request."""
        from_airport = kwargs.get("from")

        return await self.get(
            "/api/transfers",
            params={
                "from": from_airport,
                "to_lat": to_lat,
                "to_lng": to_lng,
                "to_address": to_address,
                "to_city": to_city,
                "date_time": date_time,
                "passengers": passengers,
                "type": type,
            }
        )
