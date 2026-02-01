"""Base Tool class for agent tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel


if TYPE_CHECKING:
    from policyagent.core.response import ToolResult


class ToolSchema(BaseModel):
    """Schema definition for a tool."""

    name: str
    description: str
    parameters: dict[str, Any]

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class Tool(ABC):
    """Base class for all tools.

    Tools are reusable components that agents can use to perform actions.
    Each tool has a name, description, and parameter schema.
    """

    name: ClassVar[str]
    description: ClassVar[str]

    @classmethod
    @abstractmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        """Get the JSON schema for tool parameters.

        Returns:
            JSON schema defining the parameters for this tool.
        """
        ...

    @classmethod
    def get_schema(cls) -> ToolSchema:
        """Get the complete tool schema."""
        return ToolSchema(
            name=cls.name,
            description=cls.description,
            parameters=cls.get_parameters_schema(),
        )

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            ToolResult with success/failure and output.
        """
        ...

    async def __call__(self, **kwargs: Any) -> ToolResult:
        """Call the tool (alias for execute)."""
        return await self.execute(**kwargs)
