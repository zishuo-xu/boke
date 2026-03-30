from fastapi import APIRouter, Depends

from app.application.chat.services import ChatApplicationService
from app.presentation.dependencies import get_chat_application_service
from app.presentation.schemas.session import CreateSessionRequestDTO, SessionDTO, SessionMessageDTO


router = APIRouter()


@router.get("", response_model=list[SessionDTO])
async def list_sessions(
    service: ChatApplicationService = Depends(get_chat_application_service),
) -> list[SessionDTO]:
    sessions = await service.list_sessions()
    return [
        SessionDTO(
            id=session.id,
            agentId=session.agent_id,
            title=session.title,
            messages=[
                SessionMessageDTO(role=message.role.value, content=message.content)
                for message in session.messages
            ],
        )
        for session in sessions
    ]


@router.get("/{session_id}", response_model=SessionDTO)
async def get_session(
    session_id: str,
    service: ChatApplicationService = Depends(get_chat_application_service),
) -> SessionDTO:
    session = await service.get_session(session_id)
    return SessionDTO(
        id=session.id,
        agentId=session.agent_id,
        title=session.title,
        messages=[
            SessionMessageDTO(role=message.role.value, content=message.content)
            for message in session.messages
        ],
    )


@router.post("", response_model=SessionDTO)
async def create_session(
    payload: CreateSessionRequestDTO,
    service: ChatApplicationService = Depends(get_chat_application_service),
) -> SessionDTO:
    session = await service.create_session(
        payload.session_id,
        agent_id=payload.agent_id,
        title=payload.title,
    )
    return SessionDTO(id=session.id, agentId=session.agent_id, title=session.title, messages=[])


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    service: ChatApplicationService = Depends(get_chat_application_service),
) -> None:
    await service.delete_session(session_id)
