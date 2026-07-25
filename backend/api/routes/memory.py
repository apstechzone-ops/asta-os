from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.database import get_db
from backend.memory.schemas import (
    LongTermEntry,
    ShortTermEntry,
    StructuredSearchQuery,
    VectorSearchQuery,
)
from backend.memory.service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


def get_memory_service(db: AsyncSession = Depends(get_db)) -> MemoryService:
    return MemoryService(db)


@router.post("/short-term")
async def add_short_term(entry: ShortTermEntry, memory: MemoryService = Depends(get_memory_service)):
    await memory.add_short_term(entry.session_id, entry.role, entry.content, entry.user_id)
    return {"status": "stored"}


@router.get("/sessions")
async def list_sessions(
    limit: int = 20,
    memory: MemoryService = Depends(get_memory_service),
    current_user: dict = Depends(get_current_user),
):
    return await memory.list_sessions(current_user["id"], limit)


@router.get("/short-term/{session_id}")
async def get_short_term(session_id: str, limit: int = 20, memory: MemoryService = Depends(get_memory_service)):
    return await memory.get_recent_messages(session_id, limit)


@router.post("/long-term")
async def add_long_term(entry: LongTermEntry, memory: MemoryService = Depends(get_memory_service)):
    doc_id = await memory.add_long_term(entry.user_id, entry.content, entry.metadata)
    return {"id": doc_id}


@router.post("/search")
async def search_vector(query: VectorSearchQuery, memory: MemoryService = Depends(get_memory_service)):
    return await memory.search_vector(query.query, query.top_k, query.filters)


@router.post("/search-structured")
async def search_structured(query: StructuredSearchQuery, memory: MemoryService = Depends(get_memory_service)):
    return await memory.search_structured(query.model_dump())


@router.post("/summarize/{session_id}")
async def summarize(session_id: str, memory: MemoryService = Depends(get_memory_service)):
    summary = await memory.summarize_session(session_id)
    return {"summary": summary}
