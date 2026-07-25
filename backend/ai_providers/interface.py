from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class LLMProviderError(Exception):
    """Raised when a provider fails to produce a response. The AIRouter
    catches this to trigger failover to the next provider in priority order."""


class LLMProvider(ABC):
    """Contract every AI backend (Ollama, OpenRouter, Cloudflare, ...) implements.

    Asta OS never talks to a provider's native API directly outside of
    these methods — the Planner, Memory, and Agents modules depend only
    on this interface (via AIRouter), never on a concrete provider class.
    Messages are always OpenAI-style dicts: {"role": "system"|"user"|"assistant", "content": str}.
    """

    name: str

    # Routing hints, read by AIRouter to reorder providers for a given
    # request. These are user-configured approximations (set from .env in
    # each provider's __init__), not measured/verified capabilities —
    # context_window in particular depends entirely on which model the
    # user has actually configured behind a given provider.
    context_window: int = 8192
    good_for: list[str] = ["general"]

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Non-streaming completion. Raises LLMProviderError on failure."""
        ...

    @abstractmethod
    async def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> AsyncIterator[str]:
        """Streaming completion, yields content chunks. Always raises LLMProviderError
        on failure, whether before the first chunk or mid-stream. The router can only
        safely fail over to the next provider if zero chunks were yielded before the
        error — once partial output has reached the caller, a retry would duplicate it."""
        ...

    @abstractmethod
    async def health(self) -> bool:
        """Cheap reachability check used by the router to skip dead providers."""
        ...

    @abstractmethod
    def models(self) -> list[str]:
        """Models this provider is configured to offer."""
        ...

    async def embeddings(self, texts: list[str]) -> list[list[float]]:
        """Optional. Not every provider implements this — Asta's RAG/memory
        vector search currently uses Chroma's own embedding function, not
        provider embeddings, so this has no caller yet. Present so a future
        provider (or a future RAG backend swap) can opt in without an
        interface change."""
        raise NotImplementedError(f"{self.name} does not implement embeddings()")

    def supports_tools(self) -> bool:
        """Whether this provider has native function/tool-calling support.
        Asta currently implements tool-calling at the Planner layer via
        prompt-based TOOL_CALL detection (see planner/service.py), not
        through any provider's native function-calling API — so this is
        False for all three current providers. It exists so a provider
        that DOES support native tool calls can be identified later
        without changing this interface."""
        return False

    def supports_images(self) -> bool:
        """Whether this provider can generate images."""
        return False

    def supports_vision(self) -> bool:
        """Whether this provider can accept image input (vision)."""
        return False
