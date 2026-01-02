"""
Utility Agent Tools

Tools for timezone, country info, distance, IATA codes, and date calculations.
Base URL: https://utility-agent.vercel.app
"""

from typing import Any, Dict

from app.agentic.tools.http_tool import HttpTool
from app.agentic.tools.types import ToolResult
from app.config import settings

UTILITY_AGENT_URL = getattr(settings, 'UTILITY_AGENT_URL', 'https://utility-agent.vercel.app')


class GetCityTimeTool(HttpTool):
    """Get current time and timezone information for a city."""

    def __init__(self):
        super().__init__(base_url=UTILITY_AGENT_URL)

    @property
    def name(self) -> str:
        return "get_city_time"

    @property
    def description(self) -> str:
        return (
            "Get current time and timezone information for a city. "
            "Returns local time, UTC offset, date, and day of week. "
            "Supports major cities worldwide and IATA codes."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name (e.g., 'Istanbul', 'New York', 'Tokyo') or IATA code (e.g., 'IST')",
                }
            },
            "required": ["city"],
        }

    async def execute(self, city: str, **kwargs) -> ToolResult:
        return await self.get("/api/timezone", params={"city": city})


class GetTimeDifferenceTool(HttpTool):
    """Calculate time difference between two cities."""

    def __init__(self):
        super().__init__(base_url=UTILITY_AGENT_URL)

    @property
    def name(self) -> str:
        return "get_time_difference"

    @property
    def description(self) -> str:
        return (
            "Calculate time difference between two cities. "
            "Shows current time in both cities and hour difference. "
            "Useful for planning calls or understanding jet lag."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "from_city": {
                    "type": "string",
                    "description": "Source city name (e.g., 'Istanbul')",
                },
                "to_city": {
                    "type": "string",
                    "description": "Destination city name (e.g., 'New York')",
                },
            },
            "required": ["from_city", "to_city"],
        }

    async def execute(self, from_city: str, to_city: str, **kwargs) -> ToolResult:
        return await self.get(
            "/api/timezone/difference",
            params={"from": from_city, "to": to_city},
        )


class GetCountryInfoTool(HttpTool):
    """Get practical travel information for a country or destination."""

    def __init__(self):
        super().__init__(base_url=UTILITY_AGENT_URL)

    @property
    def name(self) -> str:
        return "get_country_info"

    @property
    def description(self) -> str:
        return (
            "Get practical travel information for a country or destination. "
            "Returns plug type, voltage, emergency numbers, tipping culture, "
            "visa info, currency, language, and cultural tips. "
            "Essential for travel preparation."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Country or city name (e.g., 'Japan', 'France', 'Dubai')",
                }
            },
            "required": ["destination"],
        }

    async def execute(self, destination: str, **kwargs) -> ToolResult:
        return await self.get("/api/country", params={"destination": destination})


class GetDistanceTool(HttpTool):
    """Calculate distance between two cities."""

    def __init__(self):
        super().__init__(base_url=UTILITY_AGENT_URL)

    @property
    def name(self) -> str:
        return "get_distance"

    @property
    def description(self) -> str:
        return (
            "Calculate distance between two cities. "
            "Returns distance in km/miles and estimated flight time for long distances. "
            "Can also calculate driving/walking distance for shorter routes."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "from_city": {
                    "type": "string",
                    "description": "Origin city name (e.g., 'Istanbul')",
                },
                "to_city": {
                    "type": "string",
                    "description": "Destination city name (e.g., 'Paris')",
                },
                "mode": {
                    "type": "string",
                    "enum": ["driving-car", "foot-walking", "cycling-regular"],
                    "description": "Travel mode for route distance (optional)",
                },
            },
            "required": ["from_city", "to_city"],
        }

    async def execute(
        self,
        from_city: str,
        to_city: str,
        mode: str = None,
        **kwargs,
    ) -> ToolResult:
        params = {"from": from_city, "to": to_city}
        if mode:
            params["mode"] = mode
        return await self.get("/api/distance", params=params)


class GetDaysBetweenTool(HttpTool):
    """Calculate number of days between two dates."""

    def __init__(self):
        super().__init__(base_url=UTILITY_AGENT_URL)

    @property
    def name(self) -> str:
        return "get_days_between"

    @property
    def description(self) -> str:
        return (
            "Calculate number of days between two dates. "
            "Returns days, weeks, and day names. "
            "Useful for trip duration planning."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "from_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "to_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
            },
            "required": ["from_date", "to_date"],
        }

    async def execute(self, from_date: str, to_date: str, **kwargs) -> ToolResult:
        return await self.get("/api/days", params={"from": from_date, "to": to_date})


class LookupIATACodeTool(HttpTool):
    """Get airport information from IATA code."""

    def __init__(self):
        super().__init__(base_url=UTILITY_AGENT_URL)

    @property
    def name(self) -> str:
        return "lookup_iata_code"

    @property
    def description(self) -> str:
        return (
            "Get airport information from IATA code. "
            "Returns city, airport name, country, coordinates, and timezone. "
            "Use this to convert IATA codes to human-readable names."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "IATA airport code (e.g., 'IST', 'JFK', 'CDG')",
                }
            },
            "required": ["code"],
        }

    async def execute(self, code: str, **kwargs) -> ToolResult:
        return await self.get("/api/iata", params={"code": code.upper()})


class SearchIATAByCity(HttpTool):
    """Find IATA codes for airports in a city."""

    def __init__(self):
        super().__init__(base_url=UTILITY_AGENT_URL)

    @property
    def name(self) -> str:
        return "search_iata_by_city"

    @property
    def description(self) -> str:
        return (
            "Find IATA codes for airports in a city. "
            "Returns all airports serving that city. "
            "Use this to find the correct airport code for flight searches."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City or country name to search (e.g., 'Istanbul', 'Turkey')",
                }
            },
            "required": ["city"],
        }

    async def execute(self, city: str, **kwargs) -> ToolResult:
        return await self.get("/api/iata/search", params={"city": city})


class GetCurrentTimeTool(HttpTool):
    """Get current UTC time and date information."""

    def __init__(self):
        super().__init__(base_url=UTILITY_AGENT_URL)

    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return (
            "Get current UTC time and date information. "
            "Returns date, time, day of week, and week number. "
            "Use as a reference point for time calculations."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs) -> ToolResult:
        return await self.get("/api/now")


def get_utility_tools():
    """Get all utility tools."""
    return [
        GetCityTimeTool(),
        GetTimeDifferenceTool(),
        GetCountryInfoTool(),
        GetDistanceTool(),
        GetDaysBetweenTool(),
        LookupIATACodeTool(),
        SearchIATAByCity(),
        GetCurrentTimeTool(),
    ]
