"""OpenAI LLM client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from policyagent.core.response import LLMResponse, TokenUsage, ToolCall


if TYPE_CHECKING:
    from policyagent.config.settings import Settings
    from policyagent.core.types import JSON


class OpenAIClient:
    """OpenAI API client."""

    def __init__(self, settings: Settings) -> None:
        from openai import AsyncOpenAI  # noqa: PLC0415
        self.client = AsyncOpenAI(api_key=settings.llm.openai_api_key)
        self.model = settings.llm.openai_model

    async def chat(
        self, messages: list[JSON], tools: list[JSON] | None = None, temperature: float = 0.0,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {"model": self.model, "messages": messages, "temperature": temperature}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        response = await self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        tool_calls = [ToolCall.from_openai(tc) for tc in message.tool_calls] if message.tool_calls else []
        usage = None
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        return LLMResponse(
            content=message.content or "", tool_calls=tool_calls,
            finish_reason=response.choices[0].finish_reason or "stop", usage=usage,
        )
