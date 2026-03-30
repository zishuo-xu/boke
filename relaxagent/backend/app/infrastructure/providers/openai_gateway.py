from __future__ import annotations

from typing import AsyncIterator

import httpx

from app.domain.chat.entities import (
    ChatMessage,
    ChatRequest,
    ChatStreamEvent,
    MessageRole,
    StreamEventType,
    TokenUsage,
)
from app.infrastructure.providers.base import BaseProviderGateway


def _normalize_base_url(base_url: str) -> str:
    return base_url[:-1] if base_url.endswith("/") else base_url


class OpenAICompatibleGateway(BaseProviderGateway):
    def _build_endpoint(self, request: ChatRequest) -> str:
        return f"{_normalize_base_url(request.settings.base_url)}/chat/completions"

    def _build_headers(self, request: ChatRequest) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {request.settings.api_key}",
        }

    def _build_payload(self, request: ChatRequest) -> dict:
        return {
            "model": request.settings.model,
            "temperature": request.settings.temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
            "messages": self._build_messages(request),
        }

    def _build_test_endpoint(self, request: ChatRequest) -> str:
        return self._build_endpoint(request)

    def _build_test_headers(self, request: ChatRequest) -> dict[str, str]:
        return self._build_headers(request)

    def _build_test_payload(self, request: ChatRequest) -> dict:
        return {
            "model": request.settings.model,
            "temperature": 0,
            "stream": False,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}],
        }

    async def _parse_stream(self, response: httpx.Response) -> AsyncIterator[ChatStreamEvent]:
        async for line in response.aiter_lines():
            trimmed = line.strip()

            if not trimmed.startswith("data:"):
                continue

            data = trimmed[5:].strip()

            if data == "[DONE]":
                return

            try:
                payload = httpx.Response(200, content=data).json()
            except ValueError:
                continue

            choices = payload.get("choices") or []
            delta = choices[0].get("delta", {}).get("content") if choices else None
            usage = payload.get("usage")

            if delta:
                yield ChatStreamEvent(type=StreamEventType.TEXT_DELTA, text=delta)

            if usage:
                yield ChatStreamEvent(
                    type=StreamEventType.USAGE,
                    usage=TokenUsage(
                        input_tokens=usage.get("prompt_tokens", 0),
                        output_tokens=usage.get("completion_tokens", 0),
                    ),
                )

    def _build_messages(self, request: ChatRequest) -> list[dict[str, str]]:
        messages: list[ChatMessage] = request.messages

        if request.settings.system_prompt:
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=request.settings.system_prompt),
                *[message for message in request.messages if message.role != MessageRole.SYSTEM],
            ]

        return [{"role": message.role.value, "content": message.content} for message in messages]
