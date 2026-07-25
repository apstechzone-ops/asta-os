import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai_providers.usage import UsageLogCallback, UsageLogEntry
from backend.database.models import AIRequestLog


def make_db_usage_logger(db: AsyncSession) -> UsageLogCallback:
    """Binds a persisted logger to a specific request's DB session — AIRouter
    itself never holds a DB session (it's a long-lived singleton reused
    across every request; a shared session would be a concurrency bug)."""

    async def _log(entry: UsageLogEntry) -> None:
        row = AIRequestLog(
            user_id=uuid.UUID(entry.user_id) if entry.user_id else None,
            session_id=entry.session_id,
            provider=entry.provider,
            model=entry.model,
            task_type=entry.task_type,
            status=entry.status,
            latency_ms=entry.latency_ms,
            prompt_tokens=entry.prompt_tokens,
            completion_tokens=entry.completion_tokens,
            estimated_cost_usd=entry.estimated_cost_usd,
            fallback_index=entry.fallback_index,
            retries_configured=entry.retries_configured,
            error_message=entry.error,
        )
        db.add(row)
        await db.commit()

    return _log
