"""Base Agent class for the agent system."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from policyagent.core.message import Conversation, ToolMessage
from policyagent.core.response import AgentResponse, LLMResponse, ToolResult


if TYPE_CHECKING:
    from policyagent.core.llm import LLMClient
    from policyagent.core.tool import Tool
    from policyagent.core.types import AgentRole

logger = logging.getLogger(__name__)


class Agent(ABC):
    """Base class for all agents.

    Agents are specialized workers that use tools and LLM to accomplish tasks.
    Each agent has a role, system prompt, and set of available tools.
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: list[Tool] | None = None,
        max_iterations: int = 10,
    ) -> None:
        """Initialize the agent.

        Args:
            llm: LLM client for generating responses.
            tools: List of tools available to this agent.
            max_iterations: Maximum number of tool-use iterations.
        """
        self.llm = llm
        self.tools: dict[str, Tool] = {}
        if tools:
            for tool in tools:
                self.tools[tool.name] = tool
        self.max_iterations = max_iterations
        self.conversation = Conversation()

    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """Get the agent's role."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Get the agent's system prompt."""
        ...

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get schemas for all available tools."""
        return [tool.get_schema().to_openai_format() for tool in self.tools.values()]

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool by name with given arguments.

        Args:
            name: Name of the tool to execute.
            arguments: Arguments to pass to the tool.

        Returns:
            ToolResult from the tool execution.
        """
        if name not in self.tools:
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Tool '{name}' not found",
            )

        tool = self.tools[name]
        try:
            result = await tool.execute(**arguments)
            return result
        except Exception as e:
            logger.exception("Tool execution failed: %s", name)
            return ToolResult(
                tool_name=name,
                success=False,
                error=str(e),
            )

    async def run(self, input_data: Any) -> AgentResponse:
        """Run the agent with given input.

        Args:
            input_data: Input data for the agent to process.

        Returns:
            AgentResponse with the result.
        """
        # Reset conversation for new run
        self.conversation = Conversation()
        self.conversation.add_system(self.system_prompt)

        # Format input as user message
        user_message = self.format_input(input_data)
        self.conversation.add_user(user_message)

        total_tokens = 0
        tool_results: list[ToolResult] = []

        for iteration in range(self.max_iterations):
            logger.debug("Agent iteration %d/%d", iteration + 1, self.max_iterations)

            # Get LLM response
            response = await self.llm.chat(
                messages=self.conversation.to_openai_format(),
                tools=self.get_tool_schemas() if self.tools else None,
            )

            if response.usage:
                total_tokens += response.usage.total_tokens

            # Add assistant message to conversation
            self.conversation.add_assistant(
                content=response.content,
                tool_calls=response.tool_calls if response.has_tool_calls else None,
            )

            # If no tool calls, we're done
            if not response.has_tool_calls:
                return self.process_output(response, tool_results, total_tokens)

            # Execute tool calls
            for tool_call in response.tool_calls:
                logger.debug("Executing tool: %s", tool_call.name)
                result = await self.execute_tool(tool_call.name, tool_call.arguments)
                tool_results.append(result)

                # Add tool result to conversation
                tool_message = ToolMessage(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    content=result.to_content(),
                    is_error=not result.success,
                )
                self.conversation.add_tool_result(tool_message)

        # Max iterations reached
        return AgentResponse(
            success=False,
            error=f"Max iterations ({self.max_iterations}) reached",
            tool_results=tool_results,
            total_tokens=total_tokens,
        )

    @abstractmethod
    def format_input(self, input_data: Any) -> str:
        """Format input data as a user message.

        Args:
            input_data: Raw input data.

        Returns:
            Formatted string for user message.
        """
        ...

    @abstractmethod
    def process_output(
        self,
        response: LLMResponse,
        tool_results: list[ToolResult],
        total_tokens: int,
    ) -> AgentResponse:
        """Process the final LLM response into an AgentResponse.

        Args:
            response: Final LLM response.
            tool_results: Results from all tool executions.
            total_tokens: Total tokens used.

        Returns:
            AgentResponse with processed output.
        """
        ...
