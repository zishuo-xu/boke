from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import httpx
from time import perf_counter

from app.application.chat.services import ChatApplicationService
from app.domain.chat.entities import ChatMessage, ChatRequest, MessageRole, ModelSettings
from app.domain.chat.exceptions import InvalidChatRequestError
from app.presentation.dependencies import get_chat_application_service
from app.presentation.schemas.chat import ModelSettingsDTO


router = APIRouter()


def _categorize_provider_error(status_code: int, detail: str) -> tuple[str, str]:
    normalized = detail.lower()

    if status_code in {401, 403}:
        return "auth_error", "认证失败，请检查 API Key 是否正确。"

    if status_code == 404:
        return "endpoint_error", "接口地址不可用，请检查 Base URL 和协议类型。"

    if status_code == 429:
        return "rate_limit", "请求被限流或额度不足，请稍后重试。"

    if "model" in normalized and ("not found" in normalized or "does not exist" in normalized):
        return "model_error", "模型不可用，请检查模型名称是否正确。"

    if "invalid model" in normalized or "model" in normalized and "invalid" in normalized:
        return "model_error", "模型配置无效，请检查模型名称是否正确。"

    return "provider_error", "提供商返回错误，请检查模型、Key 和接口配置。"


@router.post("/test")
async def test_provider_connection(
    settings: ModelSettingsDTO,
    service: ChatApplicationService = Depends(get_chat_application_service),
) -> JSONResponse:
    request = ChatRequest(
        messages=[ChatMessage(role=MessageRole.USER, content="ping")],
        settings=ModelSettings(
            provider=settings.provider,
            base_url=settings.base_url,
            api_key=settings.api_key,
            model=settings.model,
            temperature=settings.temperature,
            system_prompt=settings.system_prompt,
        ),
    )

    started_at = perf_counter()

    try:
        await service.test_connection(request)
    except InvalidChatRequestError as error:
        elapsed_ms = round((perf_counter() - started_at) * 1000)
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "code": "validation_error",
                "message": str(error),
                "elapsedMs": elapsed_ms,
            },
        )
    except httpx.HTTPStatusError as error:
        elapsed_ms = round((perf_counter() - started_at) * 1000)
        detail = error.response.text or str(error)
        code, message = _categorize_provider_error(error.response.status_code, detail)
        return JSONResponse(
            status_code=error.response.status_code,
            content={
                "ok": False,
                "code": code,
                "message": message,
                "detail": detail,
                "elapsedMs": elapsed_ms,
            },
        )
    except httpx.HTTPError as error:
        elapsed_ms = round((perf_counter() - started_at) * 1000)
        return JSONResponse(
            status_code=502,
            content={
                "ok": False,
                "code": "network_error",
                "message": "无法连接到模型服务，请检查 Base URL、网络或代理设置。",
                "detail": str(error),
                "elapsedMs": elapsed_ms,
            },
        )

    elapsed_ms = round((perf_counter() - started_at) * 1000)
    return JSONResponse(
        content={
            "ok": True,
            "code": "ok",
            "message": "连接测试成功",
            "elapsedMs": elapsed_ms,
        }
    )
