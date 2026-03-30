from pydantic import BaseModel, Field, field_validator

from app.domain.chat.entities import ProviderType


class ChatMessageDTO(BaseModel):
    role: str
    content: str = Field(min_length=1)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in {"user", "assistant", "system"}:
            raise ValueError("role must be user, assistant, or system")

        return value


class ModelSettingsDTO(BaseModel):
    provider: ProviderType = ProviderType.OPENAI_COMPATIBLE
    base_url: str = Field(alias="baseURL")
    api_key: str = Field(alias="apiKey")
    model: str
    temperature: float = Field(default=0.7, ge=0, le=2)
    system_prompt: str = Field(alias="systemPrompt", default="")

    model_config = {"populate_by_name": True}


class ChatRequestDTO(BaseModel):
    messages: list[ChatMessageDTO]
    settings: ModelSettingsDTO | None = None
    session_id: str | None = Field(default=None, alias="sessionId")

    model_config = {"populate_by_name": True}
