from pydantic import BaseModel, Field


class AgentDTO(BaseModel):
    id: str
    name: str
    description: str
    provider: str
    model: str
    system_prompt: str = Field(alias="systemPrompt")

    model_config = {"populate_by_name": True}
