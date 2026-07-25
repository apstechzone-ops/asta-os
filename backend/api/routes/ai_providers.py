import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai_providers import get_ai_router
from backend.auth.dependencies import get_current_user
from backend.database import get_db
from backend.database.models import AIRequestLog

router = APIRouter(prefix="/ai/providers", tags=["ai-providers"])


@router.get("")
async def list_providers(_current_user: dict = Depends(get_current_user)):
    """Configured providers, in priority order. First = tried first."""
    ai_router = get_ai_router()
    return {"priority_order": ai_router.configured_providers()}


@router.get("/health")
async def providers_health(_current_user: dict = Depends(get_current_user)):
    """Live reachability per provider. Note: the Cloudflare check costs a
    small amount of real free-tier quota — this endpoint is for manual
    diagnostics, not something to poll continuously."""
    ai_router = get_ai_router()
    return await ai_router.health_check()


@router.get("/logs")
async def usage_logs(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The current user's own recent AI provider usage — provider, model,
    latency, estimated tokens/cost, fallback position, errors. See
    backend/ai_providers/usage.py for which fields are exact vs. estimated."""
    result = await db.execute(
        select(AIRequestLog)
        .where(AIRequestLog.user_id == uuid.UUID(current_user["id"]))
        .order_by(AIRequestLog.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "provider": r.provider,
            "model": r.model,
            "task_type": r.task_type,
            "status": r.status,
            "latency_ms": r.latency_ms,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "estimated_cost_usd": r.estimated_cost_usd,
            "fallback_index": r.fallback_index,
            "error_message": r.error_message,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
