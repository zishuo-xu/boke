from sqlalchemy import inspect, text
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.shared.config import get_settings


settings = get_settings()


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

DEFAULT_AGENTS = [
    {
        "id": "general-assistant",
        "name": "通用助手",
        "description": "通用问答和日常任务处理，适合大多数聊天场景。",
        "provider": "openai-compatible",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "system_prompt": "You are a helpful AI assistant.",
        "sort_order": 1,
    },
    {
        "id": "writing-coach",
        "name": "写作助手",
        "description": "更擅长写作润色、提纲整理和表达优化。",
        "provider": "openai-compatible",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "model": "gpt-4o-mini",
        "temperature": 0.8,
        "system_prompt": "You are a writing coach who improves clarity, tone, and structure.",
        "sort_order": 2,
    },
    {
        "id": "code-partner",
        "name": "代码助手",
        "description": "偏向代码解释、调试分析和工程实现。",
        "provider": "anthropic",
        "base_url": "https://api.anthropic.com/v1",
        "api_key": "",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.2,
        "system_prompt": "You are a senior software engineer who gives precise, practical coding help.",
        "sort_order": 3,
    },
]


def init_database() -> None:
    from app.infrastructure.persistence import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_chat_session_columns()
    _seed_default_agents()


def _ensure_chat_session_columns() -> None:
    inspector = inspect(engine)

    if "chat_sessions" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("chat_sessions")}

    if "agent_id" in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE chat_sessions ADD COLUMN agent_id VARCHAR(128) DEFAULT 'general-assistant'")
        )
        connection.execute(
            text("UPDATE chat_sessions SET agent_id = 'general-assistant' WHERE agent_id IS NULL")
        )


def _seed_default_agents() -> None:
    with engine.begin() as connection:
        for agent in DEFAULT_AGENTS:
            connection.execute(
                text(
                    """
                    INSERT OR IGNORE INTO agents
                    (id, name, description, provider, base_url, api_key, model, temperature, system_prompt, sort_order)
                    VALUES
                    (:id, :name, :description, :provider, :base_url, :api_key, :model, :temperature, :system_prompt, :sort_order)
                    """
                ),
                agent,
            )
