import pytest

from backend.ai_providers._retry import retry_async
from backend.ai_providers.interface import LLMProvider


class MinimalProvider(LLMProvider):
    """Only implements the truly abstract methods, to prove the capability
    flags and embeddings() have working, non-breaking defaults."""

    name = "minimal"

    def models(self):
        return ["minimal-model"]

    async def health(self):
        return True

    async def chat(self, messages, **kwargs):
        return "ok"

    async def stream(self, messages, **kwargs):
        yield "ok"


async def test_capability_flags_default_to_false():
    provider = MinimalProvider()
    assert provider.supports_tools() is False
    assert provider.supports_images() is False
    assert provider.supports_vision() is False


async def test_embeddings_default_raises_not_implemented():
    provider = MinimalProvider()
    with pytest.raises(NotImplementedError):
        await provider.embeddings(["some text"])


async def test_retry_async_succeeds_on_first_try():
    calls = []

    async def fn():
        calls.append(1)
        return "success"

    result = await retry_async(fn, retries=2)
    assert result == "success"
    assert len(calls) == 1


async def test_retry_async_retries_then_succeeds():
    calls = []

    async def fn():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("transient failure")
        return "success"

    result = await retry_async(fn, retries=2, base_delay=0.01)
    assert result == "success"
    assert len(calls) == 3


async def test_retry_async_raises_after_exhausting_retries():
    calls = []

    async def fn():
        calls.append(1)
        raise ConnectionError("always fails")

    with pytest.raises(ConnectionError):
        await retry_async(fn, retries=2, base_delay=0.01)
    assert len(calls) == 3
