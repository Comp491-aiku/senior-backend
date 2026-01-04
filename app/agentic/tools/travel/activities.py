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
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of activities to return (default: 10, max: 15)"
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
        limit: int = 10,
        **kwargs,
    ) -> ToolResult:
        """Execute activities search request."""
        # Cap limit to prevent token overflow (activities API doesn't respect max param)
        limit = min(limit, 15)
        
        result = await self.get(
            "/api/activities",
            params={
                "city": city,
                "lat": lat,
                "lng": lng,
                "radius": radius,
                "currency": currency,
                "max": limit,
            }
        )
        
        # CRITICAL: Truncate activities since the API returns 800+ regardless of max param
        if result.success and result.data:
            activities = result.data.get("activities", [])
            if len(activities) > limit:
                activities = activities[:limit]
            
            # Also truncate long descriptions to prevent token overflow
            for activity in activities:
                # Keep short_description, truncate long description
                if "description" in activity and len(activity["description"]) > 500:
                    activity["description"] = activity["description"][:500] + "..."
                # Limit short_description too
                if "short_description" in activity and len(activity["short_description"]) > 300:
                    activity["short_description"] = activity["short_description"][:300] + "..."
            
            result.data["activities"] = activities
            # Update output to reflect truncation
            import json
            result.output = json.dumps(result.data, indent=2, ensure_ascii=False)
        
        return result
