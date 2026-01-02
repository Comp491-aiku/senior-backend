"""
Anthropic Claude LLM Implementation

Provides AnthropicLLM class for Claude models with tool calling support.
"""

import json
from typing import Any, Dict, List, Optional

import anthropic

from app.agentic.llm.base import BaseLLM
from app.agentic.llm.types import LLMResponse, TokenUsage, ToolCall
from app.config import settings


# Token costs per MTok (USD) - Updated Jan 2026
TOKEN_COSTS: Dict[str, Dict[str, float]] = {
    # Claude 4.5 Sonnet - smart model for complex agents and coding
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    # Claude 4.5 Haiku - fastest model
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0},
    # Claude 4.5 Opus - maximum intelligence
    "claude-opus-4-5-20251101": {"input": 5.0, "output": 25.0},
}

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


class AnthropicLLM(BaseLLM):
    """
    Anthropic Claude LLM implementation.

    Converts OpenAI-style messages to Anthropic format and handles
    tool calling with Claude's native function calling.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        super().__init__(model=model, api_key=api_key)
        self._api_key = api_key or settings.ANTHROPIC_API_KEY
        self._client = anthropic.AsyncAnthropic(api_key=self._api_key)

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system: Optional[str] = None,
    ) -> LLMResponse:
        """
        Send messages to Claude and get response.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tools/functions
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            system: Optional system prompt (overridden if system msg in messages)
        """
        # Use explicit system param, may be overridden by system message in list
        system_prompt = system
        chat_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                chat_messages.append(self._convert_message(msg))

        # Build request
        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": chat_messages,
        }

        if system_prompt:
            request_kwargs["system"] = system_prompt

        if tools:
            request_kwargs["tools"] = self._convert_tools(tools)

        # Call Claude API
        response = await self._client.messages.create(**request_kwargs)

        # Parse response
        return self._parse_response(response)

    def calculate_cost(self, usage: TokenUsage) -> float:
        """Calculate cost based on token usage (costs are per MTok)."""
        costs = TOKEN_COSTS.get(self.model, TOKEN_COSTS[DEFAULT_MODEL])

        # Costs are per million tokens (MTok)
        input_cost = (usage.input_tokens / 1_000_000) * costs["input"]
        output_cost = (usage.output_tokens / 1_000_000) * costs["output"]

        return round(input_cost + output_cost, 6)

    def _convert_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAI-style message to Anthropic format."""
        role = msg["role"]
        content = msg.get("content", "")

        # Handle tool results
        if role == "tool":
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": content,
                    }
                ],
            }

        # Handle assistant messages with tool calls
        if role == "assistant" and msg.get("tool_calls"):
            content_blocks = []

            # Add text content if present
            if content:
                content_blocks.append({"type": "text", "text": content})

            # Add tool use blocks
            for tool_call in msg["tool_calls"]:
                content_blocks.append({
                    "type": "tool_use",
                    "id": tool_call["id"],
                    "name": tool_call["function"]["name"],
                    "input": json.loads(tool_call["function"]["arguments"])
                    if isinstance(tool_call["function"]["arguments"], str)
                    else tool_call["function"]["arguments"],
                })

            return {"role": "assistant", "content": content_blocks}

        # Standard message
        return {"role": role, "content": content}

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style tool schemas to Anthropic format."""
        anthropic_tools = []

        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
            else:
                # Already in Anthropic format
                anthropic_tools.append(tool)

        return anthropic_tools

    def _parse_response(self, response: anthropic.types.Message) -> LLMResponse:
        """Parse Anthropic response to LLMResponse."""
        content = ""
        tool_calls: List[ToolCall] = []

        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            model=response.model,
            usage=usage,
            raw_response=response,
        )
