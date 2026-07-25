import json
from typing import Any, AsyncIterator

import httpx

from backend.ai_providers._retry import retry_async
from backend.ai_providers.interface import LLMProvider, LLMProviderError
from backend.config import get_settings


class CloudflareProvider(LLMProvider):
    name = "cloudflare"

    def __init__(self) -> None:
        settings = get_settings()
        self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.api_token = settings.CLOUDFLARE_API_TOKEN
        self.model = settings.CLOUDFLARE_MODEL
        self.timeout = settings.CLOUDFLARE_TIMEOUT
        self.max_tokens = settings.CLOUDFLARE_MAX_TOKENS
        self.temperature = settings.CLOUDFLARE_TEMPERATURE
        self.retry_count = settings.CLOUDFLARE_RETRY_COUNT
        self.context_window = settings.CLOUDFLARE_CONTEXT_WINDOW
        self.good_for = [t.strip() for t in settings.CLOUDFLARE_GOOD_FOR.split(",") if t.strip()]
        self.cost_per_1k_input = settings.CLOUDFLARE_COST_PER_1K_INPUT
        self.cost_per_1k_output = settings.CLOUDFLARE_COST_PER_1K_OUTPUT

    @property
    def _base_url(self) -> str:
        return f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/v1"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

    def _configured(self) -> bool:
        return bool(self.account_id and self.api_token)

    def models(self) -> list[str]:
        return [self.model]

    async def health(self) -> bool:
        """Note: Cloudflare's OpenAI-compatible surface has no free ping endpoint,
        so this issues a 1-token chat request — it costs a small amount of real
        Neuron quota. The AIRouter does NOT call this on the hot path (every
        chat/stream attempt just tries the provider directly); it's for the
        manual /ai/providers/health diagnostics endpoint only."""
        if not self._configured():
            return False
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._headers(),
                    json={"model": self.model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1},
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        if not self._configured():
            raise LLMProviderError("Cloudflare account_id/api_token not configured")

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
                    f"{self._base_url}/chat/completions", headers=self._headers(), json=payload
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()

        try:
            return await retry_async(_attempt, retries=self.retry_count)
        except Exception as exc:
            raise LLMProviderError(f"Cloudflare chat failed: {exc}") from exc

    async def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> AsyncIterator[str]:
        if not self._configured():
            raise LLMProviderError("Cloudflare account_id/api_token not configured")

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
                        "POST", f"{self._base_url}/chat/completions", headers=self._headers(), json=payload
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
                    raise LLMProviderError(f"Cloudflare stream failed: {exc}") from exc
