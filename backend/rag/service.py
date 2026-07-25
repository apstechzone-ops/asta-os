import uuid
from typing import Any

from backend.memory.chroma_client import get_collection
from backend.rag.chunker import chunk_text
from backend.rag.interface import RAGInterface
from backend.rag.loader import load_text


class RAGService(RAGInterface):
    name = "rag"

    def __init__(self) -> None:
        self.collection = get_collection(name="asta_rag")

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"module": self.name, "status": "ok"}

    async def ingest_document(self, source_path: str, metadata: dict) -> str:
        doc_id = str(uuid.uuid4())
        text = load_text(source_path)
        chunks = chunk_text(text)

        ids = [f"{doc_id}:{i}" for i in range(len(chunks))]
        metadatas = [{**metadata, "doc_id": doc_id, "chunk_index": i, "source": source_path} for i in range(len(chunks))]

        if chunks:
            self.collection.add(ids=ids, documents=chunks, metadatas=metadatas)

        return doc_id

    async def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        results = self.collection.query(query_texts=[query], n_results=top_k)
        output: list[dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for i, doc, meta, dist in zip(ids, docs, metas, dists):
            output.append({"id": i, "content": doc, "metadata": meta, "score": 1 - dist})
        return output

    async def delete_document(self, doc_id: str) -> None:
        self.collection.delete(where={"doc_id": doc_id})
