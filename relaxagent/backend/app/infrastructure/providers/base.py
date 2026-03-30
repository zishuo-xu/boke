from __future__ import annotations

from typing import AsyncIterator

import httpx

from app.domain.chat.entities import ChatRequest, ChatStreamEvent


class BaseProviderGateway:
    async def stream_events(self, request: ChatRequest) -> AsyncIterator[ChatStreamEvent]:
        timeout = httpx.Timeout(connect=20.0, read=None, write=20.0, pool=20.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                self._build_endpoint(request),
                headers=self._build_headers(request),
                json=self._build_payload(request),
            ) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    raise httpx.HTTPStatusError(
                        f"Upstream request failed: {detail.decode('utf-8', errors='ignore') or response.reason_phrase}",
                        request=response.request,
                        response=response,
                    )

                async for event in self._parse_stream(response):
                    yield event

    async def test_connection(self, request: ChatRequest) -> None:
        timeout = httpx.Timeout(connect=20.0, read=20.0, write=20.0, pool=20.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                self._build_test_endpoint(request),
                headers=self._build_test_headers(request),
                json=self._build_test_payload(request),
            )

            if response.status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"Upstream request failed: {response.text or response.reason_phrase}",
                    request=response.request,
                    response=response,
                )

    def _build_endpoint(self, request: ChatRequest) -> str:
        raise NotImplementedError

    def _build_headers(self, request: ChatRequest) -> dict[str, str]:
        raise NotImplementedError

    def _build_payload(self, request: ChatRequest) -> dict:
        raise NotImplementedError

    def _build_test_endpoint(self, request: ChatRequest) -> str:
        raise NotImplementedError

    def _build_test_headers(self, request: ChatRequest) -> dict[str, str]:
        raise NotImplementedError

    def _build_test_payload(self, request: ChatRequest) -> dict:
        raise NotImplementedError

    async def _parse_stream(self, response: httpx.Response) -> AsyncIterator[ChatStreamEvent]:
        raise NotImplementedError
