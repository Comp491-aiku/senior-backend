"""
Weather Tool

Get weather forecasts for travel planning.
"""

from typing import Any, Dict

from app.agentic.tools.http_tool import HttpTool
from app.agentic.tools.types import ToolResult
from app.config import settings


class WeatherTool(HttpTool):
    """
    Get weather forecast for a destination.

    Returns daily forecasts including temperature, conditions,
    precipitation probability, and packing recommendations.
    """

    def __init__(self):
        super().__init__(base_url=settings.WEATHER_AGENT_URL)

    @property
    def name(self) -> str:
        return "get_weather_forecast"

    @property
    def description(self) -> str:
        return (
            "Get weather forecast for a destination within a date range. "
            "Returns daily forecasts including temperature, conditions, "
            "precipitation probability, and packing recommendations. "
            "Use this to help users plan what to pack and choose the best travel dates."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "City name (e.g., 'Paris', 'Istanbul', 'Tokyo', 'New York')"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format"
                }
            },
            "required": ["destination", "start_date", "end_date"]
        }

    async def execute(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        **kwargs,
    ) -> ToolResult:
        """Execute weather forecast request."""
        return await self.get(
            "/api/weather",
            params={
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
