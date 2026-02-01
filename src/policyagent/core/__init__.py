"""Core module - Base classes and shared types."""

from __future__ import annotations

from policyagent.core.agent import Agent
from policyagent.core.llm import AnthropicClient, LLMClient, OpenAIClient
from policyagent.core.message import Conversation, Message, ToolMessage
from policyagent.core.response import AgentResponse, LLMResponse, TokenUsage, ToolCall, ToolResult
from policyagent.core.tool import Tool, ToolSchema
from policyagent.core.types import AgentRole, MessageRole, RuleClassification
from policyagent.core.utils import extract_json_from_response


__all__ = [
    # Agent
    "Agent",
    # Responses
    "AgentResponse",
    # Types
    "AgentRole",
    "AnthropicClient",
    # Messages
    "Conversation",
    # LLM
    "LLMClient",
    "LLMResponse",
    "Message",
    "MessageRole",
    "OpenAIClient",
    "RuleClassification",
    "TokenUsage",
    # Tool
    "Tool",
    "ToolCall",
    "ToolMessage",
    "ToolResult",
    "ToolSchema",
    # Utils
    "extract_json_from_response",
]
