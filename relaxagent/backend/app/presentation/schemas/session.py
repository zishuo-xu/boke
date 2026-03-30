from pydantic import BaseModel, Field


class CreateSessionRequestDTO(BaseModel):
    session_id: str = Field(alias="sessionId", min_length=1)
    agent_id: str = Field(alias="agentId", min_length=1)
    title: str | None = None

    model_config = {"populate_by_name": True}


class SessionMessageDTO(BaseModel):
    role: str
    content: str


class SessionDTO(BaseModel):
    id: str
    agent_id: str = Field(alias="agentId")
    title: str
    messages: list[SessionMessageDTO]

    model_config = {"populate_by_name": True}
