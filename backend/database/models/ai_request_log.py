import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.models.mixins import TimestampMixin, UUIDPKMixin
from backend.database.session import Base


class AIRequestLog(Base, UUIDPKMixin, TimestampMixin):
    """One row per AI provider attempt (success or failure) — see
    backend/ai_providers/usage.py for exactly what each field means and
    which ones are precise vs. heuristic estimates."""

    __tablename__ = "ai_request_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    provider: Mapped[str] = mapped_column(String(50), index=True)
    model: Mapped[str] = mapped_column(String(150))
    task_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # success|failed

    latency_ms: Mapped[float] = mapped_column(Float)
    prompt_tokens: Mapped[int] = mapped_column(Integer)  # estimated — chars/4 heuristic
    completion_tokens: Mapped[int] = mapped_column(Integer)  # estimated — same heuristic
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    fallback_index: Mapped[int] = mapped_column(Integer)  # 0 = first provider tried
    retries_configured: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
