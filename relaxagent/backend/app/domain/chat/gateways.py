from typing import AsyncIterator, Protocol

from app.domain.chat.entities import ChatRequest, ChatStreamEvent


class ChatGateway(Protocol):
    async def stream_events(self, request: ChatRequest) -> AsyncIterator[ChatStreamEvent]:
        ...

    async def test_connection(self, request: ChatRequest) -> None:
        ...
