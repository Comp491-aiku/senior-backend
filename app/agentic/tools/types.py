"""
Tool Types

Type definitions for tools and tool results.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ToolType(Enum):
    """Tool classification for action tracking."""
    READ = "read"      # No side effects
    WRITE = "write"    # Has side effects
    HYBRID = "hybrid"  # Both reads and writes


class ToolResultStatus(Enum):
    """Status of tool execution."""
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ToolResult:
    """Result from tool execution."""
    output: str
    error: Optional[str] = None
    status: ToolResultStatus = ToolResultStatus.SUCCESS
    execution_time_ms: int = 0
    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == ToolResultStatus.SUCCESS

    def to_llm_format(self) -> str:
        """Format result for LLM consumption."""
        if self.success:
            return self.output
        return f"Error: {self.error}"

    @classmethod
    def success_result(cls, output: str, data: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """Create a successful result."""
        return cls(
            output=output,
            status=ToolResultStatus.SUCCESS,
            data=data or {},
        )

    @classmethod
    def error_result(cls, error: str) -> "ToolResult":
        """Create an error result."""
        return cls(
            output="",
            error=error,
            status=ToolResultStatus.ERROR,
        )
