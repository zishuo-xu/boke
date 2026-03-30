from dataclasses import dataclass
from enum import StrEnum
from typing import Optional


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ProviderType(StrEnum):
    OPENAI_COMPATIBLE = "openai-compatible"
    ANTHROPIC = "anthropic"


@dataclass(frozen=True)
class ChatMessage:
    role: MessageRole
    content: str


@dataclass(frozen=True)
class ModelSettings:
    provider: ProviderType
    base_url: str
    api_key: str
    model: str
    temperature: float
    system_prompt: str


@dataclass(frozen=True)
class ChatRequest:
    messages: list[ChatMessage]
    settings: Optional[ModelSettings] = None
    session_id: Optional[str] = None


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class ChatSession:
    id: str
    agent_id: str
    title: str
    messages: list[ChatMessage]


class StreamEventType(StrEnum):
    TEXT_DELTA = "text_delta"
    USAGE = "usage"


@dataclass(frozen=True)
class ChatStreamEvent:
    type: StreamEventType
    text: str = ""
    usage: Optional[TokenUsage] = None
