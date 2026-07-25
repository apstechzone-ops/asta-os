from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.agents import get_agent_manager
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix="/agents", tags=["agents"])


class DispatchRequest(BaseModel):
    task: dict


@router.get("")
async def list_agents(_current_user: dict = Depends(get_current_user)):
    return {"agents": get_agent_manager().list_agents()}


@router.post("/dispatch")
async def dispatch(req: DispatchRequest, _current_user: dict = Depends(get_current_user)):
    return await get_agent_manager().dispatch(req.task)
