from functools import lru_cache

from app.application.chat.services import ChatApplicationService
from app.domain.chat.services import ChatDomainService
from app.infrastructure.persistence.agent_repository import SQLAlchemyAgentRepository
from app.infrastructure.persistence.session_repository import SQLAlchemyChatSessionRepository
from app.infrastructure.providers.provider_registry import build_provider_registry


@lru_cache
def get_chat_application_service() -> ChatApplicationService:
    return ChatApplicationService(
        provider_registry=build_provider_registry(),
        session_repository=SQLAlchemyChatSessionRepository(),
        agent_repository=SQLAlchemyAgentRepository(),
        domain_service=ChatDomainService(),
    )
