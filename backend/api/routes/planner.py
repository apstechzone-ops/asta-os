from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai_providers.usage_logger import make_db_usage_logger
from backend.auth.dependencies import get_current_user
from backend.database import get_db
from backend.memory.service import MemoryService
from backend.planner.service import PlannerService
from backend.rag.service import RAGService
from backend.tools import get_tool_manager

router = APIRouter(prefix="/planner", tags=["planner"])


class ChatRequest(BaseModel):
    session_id: str
    message: str


def get_planner_service(db: AsyncSession = Depends(get_db)) -> PlannerService:
    memory = MemoryService(db)
    tool_manager = get_tool_manager()
    rag = RAGService()
    usage_logger = make_db_usage_logger(db)
    return PlannerService(memory=memory, tool_manager=tool_manager, rag=rag, usage_logger=usage_logger)


@router.post("/chat")
async def chat(
    req: ChatRequest,
    planner: PlannerService = Depends(get_planner_service),
    current_user: dict = Depends(get_current_user),
):
    print("CHAT REQUEST:", req.message)
    print("USER:", current_user)

    async def stream():
        print("STREAM START")

        try:
            async for token in planner.handle_message(
                current_user["id"],
                req.session_id,
                req.message
            ):
                print("TOKEN:", token)
                yield token

        except Exception as e:
            print("STREAM ERROR:", str(e))
            raise

    return StreamingResponse(stream(), media_type="application/x-ndjson")
