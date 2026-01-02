"""
LLM Types

Type definitions for LLM responses and tool calls.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TokenUsage:
    """Token usage statistics"""
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ToolCall:
    """Represents a tool call from the LLM"""
    id: str
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAI-compatible tool call format."""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments,
            },
        }


@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    model: str = ""
    usage: Optional[TokenUsage] = None
    raw_response: Any = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0
