from __future__ import annotations

from typing import AsyncIterator

import json
import httpx

from app.domain.chat.entities import (
    ChatRequest,
    ChatStreamEvent,
    MessageRole,
    StreamEventType,
    TokenUsage,
)
from app.infrastructure.providers.base import BaseProviderGateway


def _normalize_base_url(base_url: str) -> str:
    return base_url[:-1] if base_url.endswith("/") else base_url


class AnthropicGateway(BaseProviderGateway):
    def _build_endpoint(self, request: ChatRequest) -> str:
        return f"{_normalize_base_url(request.settings.base_url)}/messages"

    def _build_headers(self, request: ChatRequest) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "x-api-key": request.settings.api_key,
            "anthropic-version": "2023-06-01",
        }

    def _build_payload(self, request: ChatRequest) -> dict:
        return {
            "model": request.settings.model,
            "temperature": request.settings.temperature,
            "stream": True,
            "max_tokens": 4096,
            "system": request.settings.system_prompt or None,
            "messages": [
                {
                    "role": "assistant" if message.role == MessageRole.ASSISTANT else "user",
                    "content": message.content,
                }
                for message in request.messages
                if message.role != MessageRole.SYSTEM
            ],
        }

    def _build_test_endpoint(self, request: ChatRequest) -> str:
        return self._build_endpoint(request)

    def _build_test_headers(self, request: ChatRequest) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-api-key": request.settings.api_key,
            "anthropic-version": "2023-06-01",
        }

    def _build_test_payload(self, request: ChatRequest) -> dict:
        return {
            "model": request.settings.model,
            "temperature": 0,
            "stream": False,
            "max_tokens": 1,
            "system": request.settings.system_prompt or None,
            "messages": [{"role": "user", "content": "ping"}],
        }

    async def _parse_stream(self, response: httpx.Response) -> AsyncIterator[ChatStreamEvent]:
        event_type = ""
        input_tokens = 0
        output_tokens = 0

        async for line in response.aiter_lines():
            trimmed = line.strip()

            if not trimmed:
                event_type = ""
                continue

            if trimmed.startswith("event:"):
                event_type = trimmed[6:].strip()
                continue

            if not trimmed.startswith("data:"):
                continue

            data = trimmed[5:].strip()

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue

            if payload.get("type") == "message_start":
                usage = payload.get("message", {}).get("usage", {})
                input_tokens = usage.get("input_tokens", input_tokens)
                output_tokens = usage.get("output_tokens", output_tokens)

            delta = (
                payload.get("delta", {}).get("text")
                if event_type == "content_block_delta" or payload.get("type") == "content_block_delta"
                else None
            )

            if delta:
                yield ChatStreamEvent(type=StreamEventType.TEXT_DELTA, text=delta)

            usage = payload.get("usage", {})
            if usage:
                input_tokens = usage.get("input_tokens", input_tokens)
                output_tokens = usage.get("output_tokens", output_tokens)
                yield ChatStreamEvent(
                    type=StreamEventType.USAGE,
                    usage=TokenUsage(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    ),
                )

            if payload.get("type") == "message_stop":
                return
