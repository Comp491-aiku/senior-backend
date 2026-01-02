"""
Travel Agent Tools

All tools for travel planning: weather, flights, hotels, transfers, activities, exchange, utility.
"""

from app.agentic.tools.travel.weather import WeatherTool
from app.agentic.tools.travel.flights import SearchFlightsTool, AnalyzeFlightPricesTool
from app.agentic.tools.travel.hotels import SearchHotelsTool, GetHotelOffersTool
from app.agentic.tools.travel.transfers import SearchTransfersTool
from app.agentic.tools.travel.activities import SearchActivitiesTool
from app.agentic.tools.travel.exchange import (
    ConvertCurrencyTool,
    GetExchangeRatesTool,
    CalculateTravelBudgetTool,
)
from app.agentic.tools.travel.flights_api import FlightsAPITool
from app.agentic.tools.travel.utility import (
    GetCityTimeTool,
    GetTimeDifferenceTool,
    GetCountryInfoTool,
    GetDistanceTool,
    GetDaysBetweenTool,
    LookupIATACodeTool,
    SearchIATAByCity,
    GetCurrentTimeTool,
    get_utility_tools,
)


def get_all_travel_tools():
    """Get all travel agent tools."""
    return [
        # Core travel tools
        WeatherTool(),
        SearchFlightsTool(),
        AnalyzeFlightPricesTool(),
        SearchHotelsTool(),
        GetHotelOffersTool(),
        SearchTransfersTool(),
        SearchActivitiesTool(),
        ConvertCurrencyTool(),
        GetExchangeRatesTool(),
        CalculateTravelBudgetTool(),
        FlightsAPITool(),
        # Utility tools
        GetCityTimeTool(),
        GetTimeDifferenceTool(),
        GetCountryInfoTool(),
        GetDistanceTool(),
        GetDaysBetweenTool(),
        LookupIATACodeTool(),
        SearchIATAByCity(),
        GetCurrentTimeTool(),
    ]


__all__ = [
    # Core travel tools
    "WeatherTool",
    "SearchFlightsTool",
    "AnalyzeFlightPricesTool",
    "SearchHotelsTool",
    "GetHotelOffersTool",
    "SearchTransfersTool",
    "SearchActivitiesTool",
    "ConvertCurrencyTool",
    "GetExchangeRatesTool",
    "CalculateTravelBudgetTool",
    "FlightsAPITool",
    # Utility tools
    "GetCityTimeTool",
    "GetTimeDifferenceTool",
    "GetCountryInfoTool",
    "GetDistanceTool",
    "GetDaysBetweenTool",
    "LookupIATACodeTool",
    "SearchIATAByCity",
    "GetCurrentTimeTool",
    "get_utility_tools",
    "get_all_travel_tools",
]
