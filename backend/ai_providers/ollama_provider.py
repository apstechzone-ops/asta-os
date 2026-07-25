import json
from typing import Any, AsyncIterator

import httpx

from backend.ai_providers._retry import retry_async
from backend.ai_providers.interface import LLMProvider, LLMProviderError
from backend.config import get_settings


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.max_tokens = settings.OLLAMA_MAX_TOKENS
        self.temperature = settings.OLLAMA_TEMPERATURE
        self.retry_count = settings.OLLAMA_RETRY_COUNT
        self.context_window = settings.OLLAMA_CONTEXT_WINDOW
        self.good_for = [t.strip() for t in settings.OLLAMA_GOOD_FOR.split(",") if t.strip()]
        self.cost_per_1k_input = settings.OLLAMA_COST_PER_1K_INPUT
        self.cost_per_1k_output = settings.OLLAMA_COST_PER_1K_OUTPUT

    def models(self) -> list[str]:
        return [self.model]

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def _options(self) -> dict[str, Any]:
        return {"temperature": self.temperature, "num_predict": self.max_tokens}

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": False,
            "options": self._options(),
        }

        async def _attempt() -> str:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "").strip()

        try:
            return await retry_async(_attempt, retries=self.retry_count)
        except Exception as exc:
            raise LLMProviderError(f"Ollama chat failed: {exc}") from exc

    async def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> AsyncIterator[str]:
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": True,
            "options": self._options(),
        }

        for attempt in range(self.retry_count + 1):
            yielded_any = False
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yielded_any = True
                                yield content
                            if chunk.get("done"):
                                break
                return  # completed successfully
            except httpx.HTTPError as exc:
                if yielded_any or attempt >= self.retry_count:
                    raise LLMProviderError(f"Ollama stream failed: {exc}") from exc
                # else: retry from scratch — safe, since nothing reached the caller yet
