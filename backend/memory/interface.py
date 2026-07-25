from abc import abstractmethod
from typing import Any

from backend.shared import ModuleBase


class MemoryInterface(ModuleBase):
    """Contract for Memory module: short-term, long-term, project,
    knowledge memory and vector/structured search."""

    @abstractmethod
    async def add_short_term(self, session_id: str, role: str, content: str, user_id: str | None = None) -> None:
        ...

    @abstractmethod
    async def add_long_term(self, user_id: str, content: str, metadata: dict) -> str:
        ...

    @abstractmethod
    async def search_vector(
        self, query: str, top_k: int = 5, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def search_structured(self, query: dict) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_recent_messages(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def list_sessions(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def summarize_session(self, session_id: str) -> str:
        ...
