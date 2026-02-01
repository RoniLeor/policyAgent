"""Message models for agent communication."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from policyagent.core.response import ToolCall  # - Pydantic needs at runtime
from policyagent.core.types import MessageRole


class Message(BaseModel):
    """A message in the conversation."""

    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None

    model_config = {"frozen": True}


class ToolMessage(BaseModel):
    """A tool execution result message."""

    tool_call_id: str
    name: str
    content: str
    is_error: bool = False

    model_config = {"frozen": True}

    def to_message(self) -> Message:
        """Convert to a standard message."""
        return Message(
            role=MessageRole.TOOL,
            content=self.content,
            name=self.name,
            tool_call_id=self.tool_call_id,
        )


class Conversation(BaseModel):
    """A conversation history."""

    messages: list[Message] = Field(default_factory=list)

    def add(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)

    def add_system(self, content: str) -> None:
        """Add a system message."""
        self.add(Message(role=MessageRole.SYSTEM, content=content))

    def add_user(self, content: str) -> None:
        """Add a user message."""
        self.add(Message(role=MessageRole.USER, content=content))

    def add_assistant(self, content: str, tool_calls: list[ToolCall] | None = None) -> None:
        """Add an assistant message."""
        self.add(Message(role=MessageRole.ASSISTANT, content=content, tool_calls=tool_calls))

    def add_tool_result(self, tool_message: ToolMessage) -> None:
        """Add a tool result message."""
        self.add(tool_message.to_message())

    def to_openai_format(self) -> list[dict[str, Any]]:
        """Convert to OpenAI API format."""
        result: list[dict[str, Any]] = []
        for msg in self.messages:
            item: dict[str, Any] = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                item["name"] = msg.name
            if msg.tool_call_id:
                item["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                item["tool_calls"] = [tc.to_openai_format() for tc in msg.tool_calls]
            result.append(item)
        return result
