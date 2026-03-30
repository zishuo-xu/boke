from typing import Protocol

from app.domain.agent.entities import Agent


class AgentRepository(Protocol):
    async def list_agents(self) -> list[Agent]:
        ...

    async def get_agent(self, agent_id: str) -> Agent:
        ...
