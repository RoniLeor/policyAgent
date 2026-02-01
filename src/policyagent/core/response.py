"""Response models for LLM and tool outputs."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A tool call from the LLM."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    @classmethod
    def from_openai(cls, tool_call: Any) -> ToolCall:
        """Create from OpenAI tool call format."""
        args = tool_call.function.arguments
        if isinstance(args, str):
            args = json.loads(args)
        return cls(
            id=tool_call.id,
            name=tool_call.function.name,
            arguments=args,
        )

    @classmethod
    def from_anthropic(cls, tool_use: Any) -> ToolCall:
        """Create from Anthropic tool use format."""
        return cls(
            id=tool_use.id,
            name=tool_use.name,
            arguments=tool_use.input if isinstance(tool_use.input, dict) else {},
        )

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI format for conversation history."""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments),
            },
        }


class LLMResponse(BaseModel):
    """Response from an LLM call."""

    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    finish_reason: str = "stop"
    usage: TokenUsage | None = None

    @property
    def has_tool_calls(self) -> bool:
        """Check if response has tool calls."""
        return len(self.tool_calls) > 0


class TokenUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AgentResponse(BaseModel):
    """Response from an agent execution."""

    success: bool
    output: Any = None
    error: str | None = None
    tool_results: list[ToolResult] = Field(default_factory=list)
    total_tokens: int = 0


class ToolResult(BaseModel):
    """Result from a tool execution."""

    tool_name: str
    success: bool
    output: Any = None
    error: str | None = None

    def to_content(self) -> str:
        """Convert to string content for message."""
        if self.success:
            if isinstance(self.output, str):
                return self.output
            return json.dumps(self.output, indent=2, default=str)
        return f"Error: {self.error}"
