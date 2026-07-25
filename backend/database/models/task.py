import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base
from backend.database.models.mixins import TimestampMixin, UUIDPKMixin


class Task(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "tasks"

    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending|in_progress|done|cancelled
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="tasks")
    project: Mapped["Project | None"] = relationship(back_populates="tasks")
