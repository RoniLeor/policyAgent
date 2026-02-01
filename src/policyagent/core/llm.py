"""LLM client abstraction for multiple providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from policyagent.config.settings import LLMProviderEnum, Settings
from policyagent.core.response import LLMResponse


if TYPE_CHECKING:
    from policyagent.core.types import JSON


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def chat(
        self,
        messages: list[JSON],
        tools: list[JSON] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Send a chat completion request."""
        ...

    @classmethod
    def create(cls, settings: Settings | None = None, mock: bool = False) -> LLMClient:
        """Factory method to create the appropriate LLM client."""
        if mock:
            from policyagent.core.mock_llm import MockLLMClient

            return MockLLMClient()  # type: ignore[return-value]
        if settings is None:
            settings = Settings()
        if settings.llm.provider == LLMProviderEnum.OPENAI:
            from policyagent.core.providers.openai import OpenAIClient

            return OpenAIClient(settings)  # type: ignore[return-value]
        elif settings.llm.provider == LLMProviderEnum.ANTHROPIC:
            from policyagent.core.providers.anthropic import AnthropicClient

            return AnthropicClient(settings)  # type: ignore[return-value]
        else:
            msg = f"Unknown LLM provider: {settings.llm.provider}"
            raise ValueError(msg)
