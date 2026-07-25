from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.rag.service import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


def get_rag_service() -> RAGService:
    return RAGService()


class IngestRequest(BaseModel):
    source_path: str
    metadata: dict = {}


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/ingest")
async def ingest(
    req: IngestRequest,
    rag: RAGService = Depends(get_rag_service),
    _current_user: dict = Depends(get_current_user),
):
    doc_id = await rag.ingest_document(req.source_path, req.metadata)
    return {"doc_id": doc_id}


@router.post("/retrieve")
async def retrieve(
    req: RetrieveRequest,
    rag: RAGService = Depends(get_rag_service),
    _current_user: dict = Depends(get_current_user),
):
    return await rag.retrieve(req.query, req.top_k)


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    rag: RAGService = Depends(get_rag_service),
    _current_user: dict = Depends(get_current_user),
):
    await rag.delete_document(doc_id)
    return {"status": "deleted"}
