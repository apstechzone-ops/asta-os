import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base
from backend.database.models.mixins import TimestampMixin, UUIDPKMixin


class ConversationSession(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "conversation_sessions"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(150), default="New conversation")
    summary: Mapped[str] = mapped_column(Text, default="")

    messages: Mapped[list["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Message(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # user|assistant|tool|system
    content: Mapped[str] = mapped_column(Text)

    session: Mapped["ConversationSession"] = relationship(back_populates="messages")
