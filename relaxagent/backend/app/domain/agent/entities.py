from dataclasses import dataclass

from app.domain.chat.entities import ModelSettings


@dataclass(frozen=True)
class Agent:
    id: str
    name: str
    description: str
    settings: ModelSettings
