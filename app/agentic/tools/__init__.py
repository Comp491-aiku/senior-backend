"""
Tools Module

Base classes and utilities for tool implementation.
"""

from app.agentic.tools.types import ToolResult, ToolResultStatus, ToolType
from app.agentic.tools.base import BaseTool
from app.agentic.tools.http_tool import HttpTool
from app.agentic.tools.travel import (
    WeatherTool,
    SearchFlightsTool,
    AnalyzeFlightPricesTool,
    SearchHotelsTool,
    GetHotelOffersTool,
    SearchTransfersTool,
    SearchActivitiesTool,
    ConvertCurrencyTool,
    GetExchangeRatesTool,
    CalculateTravelBudgetTool,
    FlightsAPITool,
    get_all_travel_tools,
)

__all__ = [
    # Base types
    "ToolResult",
    "ToolResultStatus",
    "ToolType",
    "BaseTool",
    "HttpTool",
    # Travel tools
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
    "get_all_travel_tools",
]
