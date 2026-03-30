from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.chat.entities import ChatMessage, ChatSession, MessageRole
from app.domain.chat.exceptions import SessionNotFoundError
from app.domain.chat.repositories import ChatSessionRepository
from app.infrastructure.persistence.database import SessionLocal
from app.infrastructure.persistence.models import ChatMessageModel, ChatSessionModel


class SQLAlchemyChatSessionRepository(ChatSessionRepository):
    async def list_sessions(self) -> list[ChatSession]:
        with SessionLocal() as db:
            result = db.execute(
                select(ChatSessionModel)
                .options(selectinload(ChatSessionModel.messages))
                .order_by(ChatSessionModel.id.desc())
            )
            sessions = result.scalars().all()
            return [self._to_entity(session) for session in sessions]

    async def get_session(self, session_id: str) -> ChatSession:
        with SessionLocal() as db:
            session = self._find_session_model(db, session_id)

            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            return self._to_entity(session)

    async def create_session(
        self,
        session_id: str,
        agent_id: str,
        title: str | None = None,
    ) -> ChatSession:
        with SessionLocal() as db:
            existing = self._find_session_model(db, session_id)

            if existing:
                return self._to_entity(existing)

            session = ChatSessionModel(id=session_id, agent_id=agent_id, title=title or "新会话")
            db.add(session)
            db.commit()
            db.refresh(session)
            return self._to_entity(session)

    async def delete_session(self, session_id: str) -> None:
        with SessionLocal() as db:
            session = self._find_session_model(db, session_id)

            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            db.delete(session)
            db.commit()

    async def append_messages(self, session_id: str, messages: list[ChatMessage]) -> ChatSession:
        with SessionLocal() as db:
            session = self._find_session_model(db, session_id)

            if not session:
                session = ChatSessionModel(id=session_id, agent_id="general-assistant", title="新会话")
                db.add(session)
                db.flush()

            current_count = len(session.messages)
            for offset, message in enumerate(messages):
                db.add(
                    ChatMessageModel(
                        session_id=session.id,
                        role=message.role.value,
                        content=message.content,
                        position=current_count + offset,
                    )
                )

            db.commit()
            refreshed = self._find_session_model(db, session_id)
            assert refreshed is not None
            return self._to_entity(refreshed)

    def _find_session_model(self, db: Session, session_id: str) -> ChatSessionModel | None:
        result = db.execute(
            select(ChatSessionModel)
            .where(ChatSessionModel.id == session_id)
            .options(selectinload(ChatSessionModel.messages))
        )
        return result.scalar_one_or_none()

    def _to_entity(self, session: ChatSessionModel) -> ChatSession:
        return ChatSession(
            id=session.id,
            agent_id=session.agent_id,
            title=session.title,
            messages=[
                ChatMessage(role=MessageRole(message.role), content=message.content)
                for message in session.messages
            ],
        )
