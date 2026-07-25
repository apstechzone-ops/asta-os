from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.session import Base
from backend.database.models.mixins import TimestampMixin, UUIDPKMixin


class AgentMetadata(Base, UUIDPKMixin, TimestampMixin):
    """Registry of agents available to the Agent Manager."""

    __tablename__ = "agent_metadata"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(50))  # research|coding|google|finance|browser|memory|learning|automation
    version: Mapped[str] = mapped_column(String(20), default="0.1.0")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
