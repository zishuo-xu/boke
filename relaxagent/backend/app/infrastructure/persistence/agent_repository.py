from sqlalchemy import select

from app.domain.agent.entities import Agent
from app.domain.agent.repositories import AgentRepository
from app.domain.chat.entities import ModelSettings, ProviderType
from app.domain.chat.exceptions import AgentNotFoundError
from app.infrastructure.persistence.database import SessionLocal
from app.infrastructure.persistence.models import AgentModel


class SQLAlchemyAgentRepository(AgentRepository):
    async def list_agents(self) -> list[Agent]:
        with SessionLocal() as db:
            result = db.execute(select(AgentModel).order_by(AgentModel.sort_order.asc(), AgentModel.name.asc()))
            return [self._to_entity(agent) for agent in result.scalars().all()]

    async def get_agent(self, agent_id: str) -> Agent:
        with SessionLocal() as db:
            result = db.execute(select(AgentModel).where(AgentModel.id == agent_id))
            agent = result.scalar_one_or_none()

            if not agent:
                raise AgentNotFoundError(f"Agent 不存在: {agent_id}")

            return self._to_entity(agent)

    def _to_entity(self, agent: AgentModel) -> Agent:
        return Agent(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            settings=ModelSettings(
                provider=ProviderType(agent.provider),
                base_url=agent.base_url,
                api_key=agent.api_key,
                model=agent.model,
                temperature=agent.temperature,
                system_prompt=agent.system_prompt,
            ),
        )
