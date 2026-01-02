"""
Activities Tool

Search for tours and activities.
"""

from typing import Any, Dict, Optional

from app.agentic.tools.http_tool import HttpTool
from app.agentic.tools.types import ToolResult
from app.config import settings


class SearchActivitiesTool(HttpTool):
    """
    Search for tours and activities.

    Returns activities with descriptions, prices, ratings, and booking links.
    """

    def __init__(self):
        super().__init__(base_url=settings.ACTIVITIES_AGENT_URL, timeout=30.0)

    @property
    def name(self) -> str:
        return "search_activities"

    @property
    def description(self) -> str:
        return (
            "Search for tours, activities, and experiences in a city or location. "
            "Returns available activities with names, descriptions, prices, ratings, "
            "review counts, duration, and booking links. Use this to help users find "
            "things to do at their destination."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City code (e.g., 'PAR', 'BCN', 'IST', 'ROM'). Use this OR lat/lng."
                },
                "lat": {
                    "type": "number",
                    "description": "Latitude of the search location"
                },
                "lng": {
                    "type": "number",
                    "description": "Longitude of the search location"
                },
                "radius": {
                    "type": "integer",
                    "description": "Search radius in kilometers (default: 5)"
                },
                "currency": {
                    "type": "string",
                    "description": "Currency for prices (default: USD)"
                }
            },
            "required": []
        }

    async def execute(
        self,
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius: int = 5,
        currency: str = "USD",
        **kwargs,
    ) -> ToolResult:
        """Execute activities search request."""
        return await self.get(
            "/api/activities",
            params={
                "city": city,
                "lat": lat,
                "lng": lng,
                "radius": radius,
                "currency": currency,
            }
        )
