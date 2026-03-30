from __future__ import annotations

from typing import AsyncIterator

from app.domain.agent.repositories import AgentRepository
from app.domain.chat.entities import (
    ChatMessage,
    ChatRequest,
    ChatSession,
    ChatStreamEvent,
    MessageRole,
    ModelSettings,
    ProviderType,
)
from app.domain.chat.exceptions import UnsupportedProviderError
from app.domain.chat.gateways import ChatGateway
from app.domain.chat.repositories import ChatSessionRepository
from app.domain.chat.services import ChatDomainService


class ProviderRegistry:
    def __init__(self, providers: dict[ProviderType, ChatGateway]) -> None:
        self._providers = providers

    def get(self, provider: ProviderType) -> ChatGateway:
        gateway = self._providers.get(provider)

        if not gateway:
            raise UnsupportedProviderError(f"Unsupported provider: {provider}")

        return gateway


class ChatApplicationService:
    def __init__(
        self,
        provider_registry: ProviderRegistry,
        session_repository: ChatSessionRepository,
        agent_repository: AgentRepository,
        domain_service: ChatDomainService,
    ) -> None:
        self._provider_registry = provider_registry
        self._session_repository = session_repository
        self._agent_repository = agent_repository
        self._domain_service = domain_service

    async def stream_chat(self, request: ChatRequest) -> AsyncIterator[ChatStreamEvent]:
        self._domain_service.validate_request(request)

        resolved_request = await self._resolve_request(request)

        if request.session_id:
            latest_message = request.messages[-1]

            if latest_message.role == MessageRole.USER:
                await self._session_repository.append_messages(request.session_id, [latest_message])

        gateway = self._provider_registry.get(resolved_request.settings.provider)
        assistant_chunks: list[str] = []

        async for event in gateway.stream_events(resolved_request):
            if event.type == "text_delta" and event.text:
                assistant_chunks.append(event.text)
            yield event

        if request.session_id and assistant_chunks:
            await self._session_repository.append_messages(
                request.session_id,
                [ChatMessage(role=MessageRole.ASSISTANT, content="".join(assistant_chunks))],
            )

    async def test_connection(self, request: ChatRequest) -> None:
        self._domain_service.validate_request(request)
        assert request.settings is not None
        gateway = self._provider_registry.get(request.settings.provider)
        await gateway.test_connection(request)

    async def list_sessions(self) -> list[ChatSession]:
        return await self._session_repository.list_sessions()

    async def get_session(self, session_id: str) -> ChatSession:
        return await self._session_repository.get_session(session_id)

    async def create_session(
        self,
        session_id: str,
        agent_id: str,
        title: str | None = None,
    ) -> ChatSession:
        await self._agent_repository.get_agent(agent_id)
        return await self._session_repository.create_session(session_id, agent_id=agent_id, title=title)

    async def delete_session(self, session_id: str) -> None:
        await self._session_repository.delete_session(session_id)

    async def list_agents(self):
        return await self._agent_repository.list_agents()

    async def _resolve_request(self, request: ChatRequest) -> ChatRequest:
        if request.session_id:
            session = await self._session_repository.get_session(request.session_id)
            agent = await self._agent_repository.get_agent(session.agent_id)
            return ChatRequest(
                messages=request.messages,
                settings=ModelSettings(
                    provider=request.settings.provider if request.settings else agent.settings.provider,
                    base_url=request.settings.base_url if request.settings else agent.settings.base_url,
                    api_key=request.settings.api_key if request.settings else agent.settings.api_key,
                    model=request.settings.model if request.settings else agent.settings.model,
                    temperature=agent.settings.temperature,
                    system_prompt=agent.settings.system_prompt,
                ),
                session_id=request.session_id,
            )

        return request
