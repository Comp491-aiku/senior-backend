"""
HTTP Tool Base Class

Base class for tools that call external HTTP APIs.
"""

import json
from typing import Any, Dict, Optional

import httpx

from app.agentic.tools.base import BaseTool
from app.agentic.tools.types import ToolResult


class HttpTool(BaseTool):
    """
    Base class for tools that call external HTTP APIs.

    Provides common HTTP functionality with:
    - Async HTTP client
    - JSON response parsing
    - Error handling
    - Timeout configuration
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = headers or {}

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ToolResult:
        """
        Make an HTTP request to the external API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body for POST requests
            headers: Additional headers

        Returns:
            ToolResult with response data or error
        """
        url = f"{self.base_url}{endpoint}"

        # Merge headers
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)

        # Filter None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                )

                # Check for HTTP errors
                if response.status_code >= 400:
                    error_text = response.text
                    try:
                        error_json = response.json()
                        error_text = error_json.get("error", error_text)
                    except Exception:
                        pass
                    return ToolResult.error_result(
                        f"HTTP {response.status_code}: {error_text}"
                    )

                # Parse JSON response
                try:
                    data = response.json()
                    return ToolResult.success_result(
                        output=json.dumps(data, indent=2, ensure_ascii=False),
                        data=data,
                    )
                except Exception:
                    return ToolResult.success_result(output=response.text)

        except httpx.TimeoutException:
            return ToolResult.error_result(f"Request timeout after {self.timeout}s")
        except httpx.ConnectError:
            return ToolResult.error_result(f"Failed to connect to {self.base_url}")
        except Exception as e:
            return ToolResult.error_result(f"Request failed: {str(e)}")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ToolResult:
        """Make a GET request."""
        return await self._make_request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ToolResult:
        """Make a POST request."""
        return await self._make_request(
            "POST", endpoint, params=params, json_data=json_data, headers=headers
        )
