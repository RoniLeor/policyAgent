"""Anthropic LLM client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from policyagent.core.response import LLMResponse, TokenUsage, ToolCall


if TYPE_CHECKING:
    from policyagent.config.settings import Settings
    from policyagent.core.types import JSON


class AnthropicClient:
    """Anthropic API client."""

    def __init__(self, settings: Settings) -> None:
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic(api_key=settings.llm.anthropic_api_key)
        self.model = settings.llm.anthropic_model

    async def chat(
        self,
        messages: list[JSON],
        tools: list[JSON] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        system_content, anthropic_messages = "", []
        for msg in messages:
            role, content = msg.get("role", ""), msg.get("content", "")
            if role == "system":
                system_content += str(content) + "\n"
            elif role == "tool":
                anthropic_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.get("tool_call_id", ""),
                                "content": str(content),
                            }
                        ],
                    }
                )
            elif role == "assistant" and msg.get("tool_calls"):
                content_blocks: list[dict[str, Any]] = []
                if content:
                    content_blocks.append({"type": "text", "text": str(content)})
                tool_calls_list = msg.get("tool_calls") or []
                for tc in tool_calls_list if isinstance(tool_calls_list, list) else []:
                    if isinstance(tc, dict):
                        func = tc.get("function", {})
                        if isinstance(func, dict):
                            content_blocks.append(
                                {
                                    "type": "tool_use",
                                    "id": tc.get("id", ""),
                                    "name": func.get("name", ""),
                                    "input": func.get("arguments", {}),
                                }
                            )
                anthropic_messages.append({"role": "assistant", "content": content_blocks})
            else:
                anthropic_messages.append({"role": role, "content": str(content)})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": anthropic_messages,
            "temperature": temperature,
        }
        if system_content:
            kwargs["system"] = system_content.strip()
        if tools:
            anthropic_tools = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool.get("function")
                    if isinstance(func, dict):
                        anthropic_tools.append(
                            {
                                "name": func.get("name", ""),
                                "description": func.get("description", ""),
                                "input_schema": func.get("parameters", {}),
                            }
                        )
            kwargs["tools"] = anthropic_tools

        response = await self.client.messages.create(**kwargs)
        content, tool_calls = "", []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall.from_anthropic(block))
        usage = TokenUsage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason or "stop",
            usage=usage,
        )
