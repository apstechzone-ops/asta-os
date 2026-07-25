import uuid

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base
from backend.database.models.mixins import TimestampMixin, UUIDPKMixin


class UserSettings(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True
    )
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    voice_enabled: Mapped[bool] = mapped_column(default=True)
    wake_word: Mapped[str | None] = mapped_column(default=None)

    user: Mapped["User"] = relationship(back_populates="settings")
