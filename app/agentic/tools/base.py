"""
Base Tool Abstract Class

Provides interface for all tools used by agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.agentic.tools.types import ToolResult, ToolResultStatus, ToolType


class BaseTool(ABC):
    """
    Abstract base class for agent tools.

    Implementations must provide:
    - name: Unique tool identifier
    - description: What the tool does (shown to LLM)
    - parameters: JSON Schema for tool inputs
    - execute(): Async execution method
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this tool does (shown to LLM)."""
        pass

    @property
    def tool_type(self) -> ToolType:
        """Tool classification for action tracking."""
        return ToolType.READ

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema for tool parameters."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI-compatible tool schema for LLM."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def validate_input(self, **kwargs: Any) -> Optional[str]:
        """Validate input against parameters schema."""
        required = self.parameters.get("required", [])
        properties = self.parameters.get("properties", {})

        # Check required parameters
        for param in required:
            if param not in kwargs or kwargs[param] is None:
                return f"Missing required parameter: {param}"

        # Basic type validation
        for key, value in kwargs.items():
            if key not in properties:
                continue

            prop_schema = properties[key]
            expected_type = prop_schema.get("type")

            if expected_type == "string" and not isinstance(value, str):
                return f"Parameter '{key}' must be a string"
            elif expected_type == "integer" and not isinstance(value, int):
                return f"Parameter '{key}' must be an integer"
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return f"Parameter '{key}' must be a number"
            elif expected_type == "boolean" and not isinstance(value, bool):
                return f"Parameter '{key}' must be a boolean"

            # Check enum values
            if "enum" in prop_schema and value not in prop_schema["enum"]:
                return f"Parameter '{key}' must be one of: {prop_schema['enum']}"

        return None

    async def safe_execute(self, **kwargs: Any) -> ToolResult:
        """Execute with validation and error handling."""
        # Validate input
        validation_error = self.validate_input(**kwargs)
        if validation_error:
            return ToolResult(
                output="",
                error=validation_error,
                status=ToolResultStatus.ERROR,
            )

        # Execute with error handling
        try:
            return await self.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                output="",
                error=str(e),
                status=ToolResultStatus.ERROR,
            )
