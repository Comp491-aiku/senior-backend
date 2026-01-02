"""
FlightsAPI Tool

Custom flight search using Fast-Flights API (Google Cloud Run).
Uses Google Service Account authentication.
"""

import asyncio
import time
from typing import Any, Dict, Optional

import httpx
import google.auth.transport.requests
from google.oauth2 import service_account

from app.agentic.tools.base import BaseTool
from app.agentic.tools.types import ToolResult
from app.config import settings


class FlightsAPITool(BaseTool):
    """
    Search flights using Fast-Flights API.

    This is a custom flight API deployed on Google Cloud Run.
    Uses Google Service Account for authentication.
    """

    TOKEN_REFRESH_MARGIN = 300  # Refresh 5 minutes before expiry

    def __init__(self):
        self.base_url = settings.FLIGHTS_API_URL
        self.api_key = settings.FLIGHTS_API_KEY
        self.service_account_file = settings.GOOGLE_SERVICE_ACCOUNT_FILE

        # Token cache
        self._token: Optional[str] = None
        self._token_expiry: float = 0

        # Initialize credentials
        self._credentials = None
        self._auth_request = None

        if self.service_account_file:
            try:
                self._credentials = service_account.IDTokenCredentials.from_service_account_file(
                    self.service_account_file,
                    target_audience=self.base_url
                )
                self._auth_request = google.auth.transport.requests.Request()
            except Exception:
                pass  # Will work without auth in dev mode

    @property
    def name(self) -> str:
        return "search_flights_fast"

    @property
    def description(self) -> str:
        return (
            "Search for flights using Fast-Flights API (Google Flights data). "
            "Provides real-time flight prices and schedules. Supports one-way and "
            "round-trip searches with detailed flight information including segments "
            "and layovers. Use this for comprehensive flight search with Turkish market focus."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "from_airport": {
                    "type": "string",
                    "description": "Departure airport IATA code (e.g., 'IST', 'SAW')"
                },
                "to_airport": {
                    "type": "string",
                    "description": "Arrival airport IATA code (e.g., 'LHR', 'CDG')"
                },
                "date": {
                    "type": "string",
                    "description": "Departure date in YYYY-MM-DD format"
                },
                "return_date": {
                    "type": "string",
                    "description": "Return date for round-trip (optional)"
                },
                "adults": {
                    "type": "integer",
                    "description": "Number of adult passengers (default: 1)"
                },
                "seat": {
                    "type": "string",
                    "enum": ["economy", "premium-economy", "business", "first"],
                    "description": "Seat class (default: economy)"
                }
            },
            "required": ["from_airport", "to_airport", "date"]
        }

    def _get_token(self) -> Optional[str]:
        """Get a valid token, refreshing if necessary."""
        if not self._credentials:
            return None

        current_time = time.time()

        # Check if token needs refresh
        if self._token is None or current_time >= (self._token_expiry - self.TOKEN_REFRESH_MARGIN):
            try:
                self._credentials.refresh(self._auth_request)
                self._token = self._credentials.token
                self._token_expiry = current_time + 3600
            except Exception:
                return None

        return self._token

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with fresh token."""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    async def execute(
        self,
        from_airport: str,
        to_airport: str,
        date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        seat: str = "economy",
        **kwargs,
    ) -> ToolResult:
        """Execute flight search request."""
        import json

        try:
            params = {
                "from_airport": from_airport,
                "to_airport": to_airport,
                "date": date,
                "adults": adults,
                "seat": seat
            }

            if return_date:
                params["return_date"] = return_date

            # Refresh token in thread pool to avoid blocking
            headers = await asyncio.to_thread(self._get_headers)

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/flights/search/simple",
                    headers=headers,
                    params=params,
                )

            if response.status_code >= 400:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_text = error_json.get("detail", error_text)
                except Exception:
                    pass
                return ToolResult.error_result(f"HTTP {response.status_code}: {error_text}")

            data = response.json()
            return ToolResult.success_result(
                output=json.dumps(data, indent=2, ensure_ascii=False),
                data=data,
            )

        except httpx.TimeoutException:
            return ToolResult.error_result("Request timeout")
        except httpx.ConnectError:
            return ToolResult.error_result(f"Failed to connect to {self.base_url}")
        except Exception as e:
            return ToolResult.error_result(f"Request failed: {str(e)}")
