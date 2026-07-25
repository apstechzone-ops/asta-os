from abc import abstractmethod
from typing import Any

from backend.shared import ModuleBase


class RAGInterface(ModuleBase):
    """Contract for RAG module: document ingestion and retrieval."""

    @abstractmethod
    async def ingest_document(self, source_path: str, metadata: dict) -> str:
        ...

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def delete_document(self, doc_id: str) -> None:
        ...
