import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


async def retry_async(fn: Callable[[], Awaitable[T]], retries: int, base_delay: float = 0.5) -> T:
    """Retries an async callable. retries=1 means 2 total attempts.
    Re-raises the final exception if every attempt fails; the caller
    (each provider) wraps that in LLMProviderError."""
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return await fn()
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                await asyncio.sleep(base_delay * (attempt + 1))
    assert last_exc is not None
    raise last_exc
