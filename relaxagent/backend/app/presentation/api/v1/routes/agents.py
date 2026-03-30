from fastapi import APIRouter, Depends

from app.application.chat.services import ChatApplicationService
from app.presentation.dependencies import get_chat_application_service
from app.presentation.schemas.agent import AgentDTO


router = APIRouter()


@router.get("", response_model=list[AgentDTO])
async def list_agents(
    service: ChatApplicationService = Depends(get_chat_application_service),
) -> list[AgentDTO]:
    agents = await service.list_agents()
    return [
        AgentDTO(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            provider=agent.settings.provider.value,
            model=agent.settings.model,
            systemPrompt=agent.settings.system_prompt,
        )
        for agent in agents
    ]
