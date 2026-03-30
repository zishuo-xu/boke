import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.application.chat.services import ChatApplicationService
from app.domain.chat.entities import ChatMessage, ChatRequest, MessageRole, ModelSettings
from app.presentation.dependencies import get_chat_application_service
from app.presentation.schemas.chat import ChatRequestDTO


router = APIRouter()


@router.post("")
async def stream_chat(
    request_dto: ChatRequestDTO,
    service: ChatApplicationService = Depends(get_chat_application_service),
) -> StreamingResponse:
    request = ChatRequest(
        messages=[
            ChatMessage(role=MessageRole(message.role), content=message.content)
            for message in request_dto.messages
        ],
        settings=(
            ModelSettings(
                provider=request_dto.settings.provider,
                base_url=request_dto.settings.base_url,
                api_key=request_dto.settings.api_key,
                model=request_dto.settings.model,
                temperature=request_dto.settings.temperature,
                system_prompt=request_dto.settings.system_prompt,
            )
            if request_dto.settings
            else None
        ),
        session_id=request_dto.session_id,
    )

    async def event_stream():
        async for event in service.stream_chat(request):
            if event.type == "text_delta":
                yield json.dumps({"type": event.type, "text": event.text}, ensure_ascii=False) + "\n"
            elif event.type == "usage" and event.usage:
                yield (
                    json.dumps(
                        {
                            "type": event.type,
                            "inputTokens": event.usage.input_tokens,
                            "outputTokens": event.usage.output_tokens,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    return StreamingResponse(event_stream(), media_type="application/x-ndjson; charset=utf-8")
