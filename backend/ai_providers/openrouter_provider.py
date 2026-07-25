import json
from typing import Any, AsyncIterator

import httpx

from backend.ai_providers._retry import retry_async
from backend.ai_providers.interface import LLMProvider, LLMProviderError
from backend.config import get_settings

BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.timeout = settings.OPENROUTER_TIMEOUT
        self.max_tokens = settings.OPENROUTER_MAX_TOKENS
        self.temperature = settings.OPENROUTER_TEMPERATURE
        self.retry_count = settings.OPENROUTER_RETRY_COUNT
        self.context_window = settings.OPENROUTER_CONTEXT_WINDOW
        self.good_for = [t.strip() for t in settings.OPENROUTER_GOOD_FOR.split(",") if t.strip()]
        self.cost_per_1k_input = settings.OPENROUTER_COST_PER_1K_INPUT
        self.cost_per_1k_output = settings.OPENROUTER_COST_PER_1K_OUTPUT

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter uses these for its free-tier leaderboard attribution; safe to send always.
            "HTTP-Referer": "https://asta.os",
            "X-Title": "Asta OS",
        }

    def models(self) -> list[str]:
        return [self.model]

    async def health(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{BASE_URL}/models", headers=self._headers())
                return resp.status_code == 200
        except Exception:
            return False

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        if not self.api_key:
            raise LLMProviderError("OpenRouter API key not configured")

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": False,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        async def _attempt() -> str:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{BASE_URL}/chat/completions", headers=self._headers(), json=payload
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()

        try:
            return await retry_async(_attempt, retries=self.retry_count)
        except Exception as exc:
            raise LLMProviderError(f"OpenRouter chat failed: {exc}") from exc

    async def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> AsyncIterator[str]:
        if not self.api_key:
            raise LLMProviderError("OpenRouter API key not configured")

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": True,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        for attempt in range(self.retry_count + 1):
            yielded_any = False
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream(
                        "POST", f"{BASE_URL}/chat/completions", headers=self._headers(), json=payload
                    ) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line or not line.startswith("data: "):
                                continue
                            data_str = line[len("data: "):].strip()
                            if data_str == "[DONE]":
                                break
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yielded_any = True
                                yield content
                return
            except httpx.HTTPError as exc:
                if yielded_any or attempt >= self.retry_count:
                    raise LLMProviderError(f"OpenRouter stream failed: {exc}") from exc
