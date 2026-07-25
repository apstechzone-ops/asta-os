from typing import AsyncIterator

import pytest

from backend.ai_providers.interface import LLMProvider, LLMProviderError
from backend.ai_providers.router import AIRouter, AllProvidersFailedError


class FakeProvider(LLMProvider):
    """A configurable fake provider for testing router failover logic
    without hitting any real network endpoint."""

    def __init__(
        self,
        name: str,
        fail: bool = False,
        chunks: list[str] | None = None,
        fail_after: int = 0,
        context_window: int = 8192,
        good_for: list[str] | None = None,
    ):
        self.name = name
        self._fail = fail
        self._chunks = chunks or ["hello"]
        self._fail_after = fail_after  # yield this many chunks, then fail
        self.context_window = context_window
        self.good_for = good_for or ["general"]

    def models(self) -> list[str]:
        return ["fake-model"]

    async def health(self) -> bool:
        return not self._fail

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        if self._fail:
            raise LLMProviderError(f"{self.name} is down")
        return f"{self.name}: response"

    async def stream(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        if self._fail_after == 0 and self._fail:
            raise LLMProviderError(f"{self.name} is down")

        yielded = 0
        for chunk in self._chunks:
            if self._fail_after and yielded >= self._fail_after:
                raise LLMProviderError(f"{self.name} died mid-stream")
            yield chunk
            yielded += 1

        if self._fail and self._fail_after == 0:
            raise LLMProviderError(f"{self.name} is down")


def make_router(*providers: LLMProvider) -> AIRouter:
    router = AIRouter.__new__(AIRouter)  # bypass __init__'s config-file loading
    router.providers = list(providers)
    return router


async def test_chat_uses_first_healthy_provider():
    router = make_router(FakeProvider("primary"), FakeProvider("backup"))
    result = await router.chat([{"role": "user", "content": "hi"}])
    assert result == "primary: response"


async def test_chat_fails_over_to_second_provider():
    router = make_router(FakeProvider("primary", fail=True), FakeProvider("backup"))
    result = await router.chat([{"role": "user", "content": "hi"}])
    assert result == "backup: response"


async def test_chat_all_providers_fail_raises_with_all_attempts():
    router = make_router(FakeProvider("primary", fail=True), FakeProvider("backup", fail=True))
    with pytest.raises(AllProvidersFailedError) as exc_info:
        await router.chat([{"role": "user", "content": "hi"}])
    assert "primary" in exc_info.value.attempts
    assert "backup" in exc_info.value.attempts


async def test_stream_uses_first_healthy_provider():
    router = make_router(
        FakeProvider("primary", chunks=["a", "b", "c"]),
        FakeProvider("backup", chunks=["x", "y"]),
    )
    result = [chunk async for chunk in router.stream([{"role": "user", "content": "hi"}])]
    assert result == ["a", "b", "c"]


async def test_stream_fails_over_before_any_chunk_yielded():
    router = make_router(
        FakeProvider("primary", fail=True),
        FakeProvider("backup", chunks=["x", "y"]),
    )
    result = [chunk async for chunk in router.stream([{"role": "user", "content": "hi"}])]
    assert result == ["x", "y"]


async def test_stream_does_not_retry_after_partial_output():
    """Critical safety property: if a provider yields some chunks then dies,
    the router must NOT silently retry with another provider — that would
    duplicate content the caller already received."""
    router = make_router(
        FakeProvider("primary", chunks=["a", "b", "c"], fail_after=2),
        FakeProvider("backup", chunks=["x", "y"]),
    )
    received = []
    with pytest.raises(AllProvidersFailedError):
        async for chunk in router.stream([{"role": "user", "content": "hi"}]):
            received.append(chunk)

    assert received == ["a", "b"]  # got the pre-failure chunks, then it stopped — no fallback content


async def test_configured_providers_reflects_priority_order():
    router = make_router(FakeProvider("primary"), FakeProvider("backup"))
    assert router.configured_providers() == ["primary", "backup"]


def test_estimate_tokens_uses_chars_per_token_heuristic():
    messages = [{"role": "user", "content": "x" * 400}]
    assert AIRouter.estimate_tokens(messages) == 100


def test_classify_task_detects_coding_signals():
    assert AIRouter.classify_task("here's a python function:\n```def foo(): pass```") == "coding"
    assert AIRouter.classify_task("I'm getting a traceback in my app") == "coding"


def test_classify_task_defaults_to_general():
    assert AIRouter.classify_task("what's the weather like today?") == "general"


async def test_ordered_providers_prefers_task_match_without_excluding_others():
    router = make_router(
        FakeProvider("general_only", good_for=["general"]),
        FakeProvider("coding_capable", good_for=["general", "coding"]),
    )
    ordered = router._ordered_providers([{"role": "user", "content": "fix this bug"}], task_type="coding")
    assert [p.name for p in ordered] == ["coding_capable", "general_only"]


async def test_ordered_providers_preserves_priority_when_no_task_type():
    router = make_router(
        FakeProvider("primary", good_for=["general"]),
        FakeProvider("backup", good_for=["general", "coding"]),
    )
    ordered = router._ordered_providers([{"role": "user", "content": "hi"}], task_type=None)
    assert [p.name for p in ordered] == ["primary", "backup"]


async def test_ordered_providers_deprioritizes_undersized_context_window():
    router = make_router(
        FakeProvider("small_context", context_window=100),
        FakeProvider("large_context", context_window=1_000_000),
    )
    huge_message = [{"role": "user", "content": "x" * 20_000}]
    ordered = router._ordered_providers(huge_message, task_type=None)
    assert [p.name for p in ordered] == ["large_context", "small_context"]


async def test_ordered_providers_still_tries_undersized_provider_as_fallback():
    """Reordering must never exclude a provider outright — if every other
    provider fails, the 'wrong-sized' one is still attempted."""
    router = make_router(
        FakeProvider("large_context_but_down", context_window=1_000_000, fail=True),
        FakeProvider("small_context_works", context_window=100, chunks=["ok"]),
    )
    huge_message = [{"role": "user", "content": "x" * 20_000}]
    result = "".join([chunk async for chunk in router.stream(huge_message)])
    assert result == "ok"


async def test_chat_and_stream_accept_task_type_without_breaking():
    router = make_router(FakeProvider("primary", good_for=["coding"]))
    result = await router.chat([{"role": "user", "content": "hi"}], task_type="coding")
    assert result == "primary: response"
