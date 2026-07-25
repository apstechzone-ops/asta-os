import time
from typing import Any, AsyncIterator

from backend.ai_providers.cloudflare_provider import CloudflareProvider
from backend.ai_providers.interface import LLMProvider, LLMProviderError
from backend.ai_providers.ollama_provider import OllamaProvider
from backend.ai_providers.openrouter_provider import OpenRouterProvider
from backend.ai_providers.usage import UsageLogCallback, UsageLogEntry
from backend.config import get_settings
from backend.logging_ import get_logger

logger = get_logger(__name__)

_PROVIDER_CLASSES: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openrouter": OpenRouterProvider,
    "cloudflare": CloudflareProvider,
}


class AllProvidersFailedError(Exception):
    def __init__(self, attempts: dict[str, str]):
        self.attempts = attempts
        summary = "; ".join(f"{name}: {err}" for name, err in attempts.items())
        super().__init__(f"All configured AI providers failed — {summary}")


class AIRouter:
    """Model-agnostic entrypoint for every reasoning call in Asta OS.

    Priority order comes from AI_PROVIDER_PRIORITY (.env), e.g. "ollama,openrouter,cloudflare".
    Providers are tried in that order; on failure the router moves to the next one.
    No code changes are needed to reorder, add, or drop a provider — it's config-driven.

    Optional per-request routing hints (task_type, or an estimated prompt size
    large enough to matter) reorder that base priority list before the failover
    loop runs — they never remove a provider from consideration, only reprioritize.

    An optional on_log callback (see ai_providers/usage.py) receives one
    UsageLogEntry per provider attempt — success or failure. AIRouter has no
    idea what happens to that callback (write to DB, stdout, nowhere) — that
    decoupling is deliberate, matching every other DI boundary in this codebase.
    """

    _CHARS_PER_TOKEN_ESTIMATE = 4
    _CONTEXT_SAFETY_MARGIN = 1.25

    def __init__(self, priority: list[str] | None = None) -> None:
        settings = get_settings()
        names = priority or [p.strip() for p in settings.AI_PROVIDER_PRIORITY.split(",") if p.strip()]

        self.providers: list[LLMProvider] = []
        for name in names:
            provider_cls = _PROVIDER_CLASSES.get(name)
            if provider_cls is None:
                logger.warning("Unknown AI provider in priority list, skipping: %s", name)
                continue
            self.providers.append(provider_cls())

        if not self.providers:
            raise ValueError(
                "No valid AI providers configured. Check AI_PROVIDER_PRIORITY in .env "
                f"(known providers: {list(_PROVIDER_CLASSES)})"
            )

    @staticmethod
    def estimate_tokens(messages: list[dict[str, str]]) -> int:
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // AIRouter._CHARS_PER_TOKEN_ESTIMATE

    @staticmethod
    def _estimate_completion_tokens(text: str) -> int:
        return len(text) // AIRouter._CHARS_PER_TOKEN_ESTIMATE

    @staticmethod
    def classify_task(message: str) -> str:
        lowered = message.lower()
        coding_signals = ("```", "def ", "function ", "class ", "traceback", "stack trace", "bug", " error:", "npm ", "pip install")
        if any(signal in lowered for signal in coding_signals):
            return "coding"
        return "general"

    def _ordered_providers(self, messages: list[dict[str, str]], task_type: str | None) -> list[LLMProvider]:
        estimated_tokens = self.estimate_tokens(messages)
        required_tokens = int(estimated_tokens * self._CONTEXT_SAFETY_MARGIN)

        def fits_context(p: LLMProvider) -> bool:
            return p.context_window >= required_tokens

        def matches_task(p: LLMProvider) -> bool:
            return task_type is None or task_type in p.good_for

        def score(p: LLMProvider) -> tuple[int, int]:
            return (0 if fits_context(p) else 1, 0 if matches_task(p) else 1)

        return sorted(self.providers, key=score)

    @staticmethod
    def _estimate_cost(provider: LLMProvider, prompt_tokens: int, completion_tokens: int) -> float:
        cost_in = getattr(provider, "cost_per_1k_input", 0.0)
        cost_out = getattr(provider, "cost_per_1k_output", 0.0)
        return round((prompt_tokens / 1000) * cost_in + (completion_tokens / 1000) * cost_out, 6)

    def _model_name(self, provider: LLMProvider) -> str:
        models = provider.models()
        return models[0] if models else ""

    async def _emit_log(
        self,
        on_log: UsageLogCallback | None,
        *,
        provider: LLMProvider,
        status: str,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        fallback_index: int,
        task_type: str | None,
        session_id: str | None,
        user_id: str | None,
        error: str | None = None,
    ) -> None:
        if on_log is None:
            return
        entry = UsageLogEntry(
            provider=provider.name,
            model=self._model_name(provider),
            status=status,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost_usd=self._estimate_cost(provider, prompt_tokens, completion_tokens),
            fallback_index=fallback_index,
            retries_configured=getattr(provider, "retry_count", 0),
            task_type=task_type,
            session_id=session_id,
            user_id=user_id,
            error=error,
        )
        try:
            await on_log(entry)
        except Exception:
            logger.exception("Usage log callback raised — swallowing so logging never breaks a chat request")

    async def chat(
        self,
        messages: list[dict[str, str]],
        task_type: str | None = None,
        on_log: UsageLogCallback | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        attempts: dict[str, str] = {}
        prompt_tokens = self.estimate_tokens(messages)

        for idx, provider in enumerate(self._ordered_providers(messages, task_type)):
            start = time.monotonic()
            try:
                result = await provider.chat(messages, **kwargs)
                latency_ms = (time.monotonic() - start) * 1000
                completion_tokens = self._estimate_completion_tokens(result)
                await self._emit_log(
                    on_log, provider=provider, status="success", latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                    fallback_index=idx, task_type=task_type, session_id=session_id, user_id=user_id,
                )
                return result
            except LLMProviderError as exc:
                latency_ms = (time.monotonic() - start) * 1000
                logger.warning("Provider %s failed, trying next: %s", provider.name, exc)
                attempts[provider.name] = str(exc)
                await self._emit_log(
                    on_log, provider=provider, status="failed", latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens, completion_tokens=0,
                    fallback_index=idx, task_type=task_type, session_id=session_id, user_id=user_id,
                    error=str(exc),
                )
        raise AllProvidersFailedError(attempts)

    async def stream(
        self,
        messages: list[dict[str, str]],
        task_type: str | None = None,
        on_log: UsageLogCallback | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Fails over between providers ONLY if the failure happens before any
        chunk has been yielded. Once output has reached the caller, a mid-stream
        failure propagates as AllProvidersFailedError rather than silently
        retrying (which would duplicate already-sent content)."""
        attempts: dict[str, str] = {}
        prompt_tokens = self.estimate_tokens(messages)

        for idx, provider in enumerate(self._ordered_providers(messages, task_type)):
            yielded_any = False
            accumulated = ""
            start = time.monotonic()
            try:
                async for chunk in provider.stream(messages, **kwargs):
                    yielded_any = True
                    accumulated += chunk
                    yield chunk
                latency_ms = (time.monotonic() - start) * 1000
                await self._emit_log(
                    on_log, provider=provider, status="success", latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=self._estimate_completion_tokens(accumulated),
                    fallback_index=idx, task_type=task_type, session_id=session_id, user_id=user_id,
                )
                return  # provider completed successfully
            except LLMProviderError as exc:
                latency_ms = (time.monotonic() - start) * 1000
                logger.warning("Provider %s failed, trying next: %s", provider.name, exc)
                attempts[provider.name] = str(exc)
                await self._emit_log(
                    on_log, provider=provider, status="failed", latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=self._estimate_completion_tokens(accumulated),
                    fallback_index=idx, task_type=task_type, session_id=session_id, user_id=user_id,
                    error=str(exc),
                )
                if yielded_any:
                    raise AllProvidersFailedError(attempts) from exc
        raise AllProvidersFailedError(attempts)

    async def health_check(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for provider in self.providers:
            results[provider.name] = await provider.health()
        return results

    def configured_providers(self) -> list[str]:
        return [p.name for p in self.providers]


_router_singleton: AIRouter | None = None


def get_ai_router() -> AIRouter:
    global _router_singleton
    if _router_singleton is None:
        _router_singleton = AIRouter()
    return _router_singleton
