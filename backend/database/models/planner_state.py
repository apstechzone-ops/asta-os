import uuid

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.session import Base
from backend.database.models.mixins import TimestampMixin, UUIDPKMixin


class PlannerState(Base, UUIDPKMixin, TimestampMixin):
    """Persisted planner session state so conversations can resume."""

    __tablename__ = "planner_state"

    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict)  # working memory / scratchpad
    active_tool: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="idle")  # idle|thinking|executing_tool|done
