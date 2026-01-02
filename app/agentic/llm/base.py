"""
Base LLM Abstract Class

Provides interface for LLM implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.agentic.llm.types import LLMResponse, TokenUsage


class BaseLLM(ABC):
    """
    Abstract base class for LLM providers.

    Implementations must provide:
    - chat(): Async chat completion with tool support
    - calculate_cost(): Cost calculation based on token usage
    """

    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model
        self._api_key = api_key

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Send messages to LLM and get response.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool schemas
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with content and optional tool calls
        """
        pass

    @abstractmethod
    def calculate_cost(self, usage: TokenUsage) -> float:
        """
        Calculate cost based on token usage.

        Args:
            usage: Token usage statistics

        Returns:
            Cost in USD
        """
        pass
