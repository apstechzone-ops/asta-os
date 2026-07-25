from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable


@dataclass
class UsageLogEntry:
    provider: str
    model: str
    status: str  # "success" | "failed"
    latency_ms: float
    prompt_tokens: int  # estimated via chars/4 heuristic — see AIRouter.estimate_tokens
    completion_tokens: int  # same heuristic, applied to the response
    estimated_cost_usd: float  # computed from provider.cost_per_1k_input/output; 0.0 for free-tier config
    fallback_index: int  # 0 = first provider tried succeeded/failed, 1 = second, etc. — accurately known
    retries_configured: int  # the provider's configured retry_count, NOT a count of retries actually
    # consumed for this specific call — AIRouter cannot observe intra-provider
    # retry attempts without changing the chat()/stream() -> str/AsyncIterator[str]
    # contract that other code already depends on. Labeled honestly rather than
    # silently presented as an exact count.
    task_type: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


UsageLogCallback = Callable[[UsageLogEntry], Awaitable[None]]
