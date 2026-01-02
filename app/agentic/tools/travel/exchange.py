"""
Exchange Tools

Currency conversion and exchange rates.
"""

from typing import Any, Dict, Optional

from app.agentic.tools.http_tool import HttpTool
from app.agentic.tools.types import ToolResult
from app.config import settings


class ConvertCurrencyTool(HttpTool):
    """
    Convert currency amounts.

    Converts an amount from one currency to another (or multiple currencies).
    """

    def __init__(self):
        super().__init__(base_url=settings.EXCHANGE_AGENT_URL, timeout=15.0)

    @property
    def name(self) -> str:
        return "convert_currency"

    @property
    def description(self) -> str:
        return (
            "Convert an amount from one currency to another. Can convert to multiple "
            "currencies at once. Returns exchange rate and converted amount. "
            "Use this when users need to know how much their money is worth in another currency."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "from": {
                    "type": "string",
                    "description": "Source currency code (e.g., 'USD', 'EUR', 'TRY')"
                },
                "to": {
                    "type": "string",
                    "description": "Target currency code(s), comma-separated for multiple (e.g., 'TRY' or 'USD,EUR,GBP')"
                },
                "amount": {
                    "type": "number",
                    "description": "Amount to convert"
                }
            },
            "required": ["from", "to", "amount"]
        }

    async def execute(self, to: str, amount: float, **kwargs) -> ToolResult:
        """Execute currency conversion request."""
        from_currency = kwargs.get("from")

        return await self.get(
            "/api/convert",
            params={
                "from": from_currency,
                "to": to,
                "amount": amount,
            }
        )


class GetExchangeRatesTool(HttpTool):
    """
    Get exchange rates.

    Returns current exchange rates for a base currency.
    """

    def __init__(self):
        super().__init__(base_url=settings.EXCHANGE_AGENT_URL, timeout=15.0)

    @property
    def name(self) -> str:
        return "get_exchange_rates"

    @property
    def description(self) -> str:
        return (
            "Get current exchange rates for a base currency. Can filter to specific "
            "target currencies. Use this when users want to see current rates or compare "
            "multiple currencies."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base": {
                    "type": "string",
                    "description": "Base currency code (default: USD)"
                },
                "symbols": {
                    "type": "string",
                    "description": "Comma-separated currency codes to filter (optional)"
                }
            },
            "required": []
        }

    async def execute(
        self,
        base: str = "USD",
        symbols: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """Execute exchange rates request."""
        return await self.get(
            "/api/rates",
            params={
                "base": base,
                "symbols": symbols,
            }
        )


class CalculateTravelBudgetTool(HttpTool):
    """
    Calculate travel budget in different currencies.

    Converts a travel budget to popular destination currencies.
    """

    def __init__(self):
        super().__init__(base_url=settings.EXCHANGE_AGENT_URL, timeout=15.0)

    @property
    def name(self) -> str:
        return "calculate_travel_budget"

    @property
    def description(self) -> str:
        return (
            "Convert a travel budget to popular destination currencies. Shows how much "
            "money the user will have in different countries. Useful for trip planning and budgeting."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "from": {
                    "type": "string",
                    "description": "Source currency code (default: USD)"
                },
                "amount": {
                    "type": "number",
                    "description": "Budget amount to convert"
                },
                "destinations": {
                    "type": "string",
                    "description": "Comma-separated currency codes for specific destinations (optional)"
                }
            },
            "required": ["amount"]
        }

    async def execute(
        self,
        amount: float,
        destinations: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """Execute travel budget calculation request."""
        from_currency = kwargs.get("from", "USD")

        return await self.get(
            "/api/travel-budget",
            params={
                "from": from_currency,
                "amount": amount,
                "destinations": destinations,
            }
        )
