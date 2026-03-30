from typing import Protocol

from app.domain.chat.entities import ChatMessage, ChatSession


class ChatSessionRepository(Protocol):
    async def list_sessions(self) -> list[ChatSession]:
        ...

    async def get_session(self, session_id: str) -> ChatSession:
        ...

    async def create_session(
        self,
        session_id: str,
        agent_id: str,
        title: str | None = None,
    ) -> ChatSession:
        ...

    async def delete_session(self, session_id: str) -> None:
        ...

    async def append_messages(self, session_id: str, messages: list[ChatMessage]) -> ChatSession:
        ...
