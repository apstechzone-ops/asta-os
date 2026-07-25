from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import get_settings


@lru_cache
def get_chroma_client() -> chromadb.ClientAPI:
    settings = get_settings()
    return chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_collection(name: str = "asta_memory", client: chromadb.ClientAPI | None = None):
    client = client or get_chroma_client()
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
