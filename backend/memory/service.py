import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai_providers import AllProvidersFailedError, get_ai_router
from backend.database.models import ConversationSession, Message
from backend.memory.chroma_client import get_collection
from backend.memory.interface import MemoryInterface

SUMMARY_PROMPT = (
    "Summarize the following conversation in 3-5 concise sentences, "
    "capturing key facts, decisions and open questions:\n\n{transcript}"
)


def _to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class MemoryService(MemoryInterface):
    name = "memory"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = get_collection()
        return self._collection

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"module": self.name, "status": "ok"}

    # ---- short-term (conversation) memory ----

    async def add_short_term(self, session_id: str, role: str, content: str, user_id: str | None = None) -> None:
        session_uuid = _to_uuid(session_id)
        result = await self.db.execute(
            select(ConversationSession).where(ConversationSession.id == session_uuid)
        )
        session = result.scalar_one_or_none()
        if session is None:
            session = ConversationSession(id=session_uuid, user_id=_to_uuid(user_id) if user_id else None)
            self.db.add(session)
            await self.db.flush()
        elif user_id and session.user_id is None:
            session.user_id = _to_uuid(user_id)

        self.db.add(Message(session_id=session.id, role=role, content=content))
        await self.db.commit()

    async def list_sessions(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(ConversationSession)
            .where(ConversationSession.user_id == _to_uuid(user_id))
            .order_by(ConversationSession.updated_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()

        output: list[dict[str, Any]] = []
        for session in sessions:
            last_msg_result = await self.db.execute(
                select(Message)
                .where(Message.session_id == session.id)
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            last_message = last_msg_result.scalar_one_or_none()
            output.append(
                {
                    "id": str(session.id),
                    "title": session.title,
                    "summary": session.summary,
                    "last_message": last_message.content if last_message else "",
                    "updated_at": session.updated_at.isoformat(),
                }
            )
        return output

    async def get_recent_messages(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == _to_uuid(session_id))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))
        return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in messages]

    # ---- long-term (vector) memory ----

    async def add_long_term(self, user_id: str, content: str, metadata: dict) -> str:
        doc_id = str(uuid.uuid4())
        meta = {"user_id": user_id, **metadata}
        self.collection.add(ids=[doc_id], documents=[content], metadatas=[meta])
        return doc_id

    async def search_vector(
        self, query: str, top_k: int = 5, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        results = self.collection.query(query_texts=[query], n_results=top_k, where=filters)
        output: list[dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for i, doc, meta, dist in zip(ids, docs, metas, dists):
            output.append({"id": i, "content": doc, "metadata": meta, "score": 1 - dist})
        return output

    # ---- structured (SQL) search ----

    async def search_structured(self, query: dict) -> list[dict[str, Any]]:
        """query = {table, filters, limit}. Minimal generic filter-by-equality search."""
        from backend.database import models as model_module

        table_name = query.get("table")
        model_cls = getattr(model_module, table_name, None)
        if model_cls is None:
            raise ValueError(f"Unknown table/model: {table_name}")

        stmt = select(model_cls)
        for field, value in (query.get("filters") or {}).items():
            column = getattr(model_cls, field, None)
            if column is not None:
                stmt = stmt.where(column == value)
        stmt = stmt.limit(query.get("limit", 20))

        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return [
            {c.name: getattr(row, c.name) for c in row.__table__.columns}
            for row in rows
        ]

    # ---- summarization ----

    async def summarize_session(self, session_id: str) -> str:
        messages = await self.get_recent_messages(session_id, limit=50)
        if not messages:
            return ""

        transcript = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        try:
            router = get_ai_router()
            summary = await router.chat(
                [{"role": "user", "content": SUMMARY_PROMPT.format(transcript=transcript)}]
            )
        except AllProvidersFailedError:
            # Every provider unreachable: fall back to a truncated extractive summary.
            summary = transcript[:500]

        result = await self.db.execute(
            select(ConversationSession).where(ConversationSession.id == _to_uuid(session_id))
        )
        session = result.scalar_one_or_none()
        if session is not None:
            session.summary = summary
            await self.db.commit()

        return summary
