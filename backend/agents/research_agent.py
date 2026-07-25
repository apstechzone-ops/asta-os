from typing import Any

from backend.agents.interface import AgentInterface
from backend.ai_providers import AIRouter, AllProvidersFailedError, get_ai_router


class ResearchAgent(AgentInterface):
    name = "research_agent"

    def __init__(self, ai_router: AIRouter | None = None) -> None:
        self.ai_router = ai_router or get_ai_router()

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"module": self.name, "status": "ok"}

    async def can_handle(self, task: dict) -> bool:
        return task.get("type") == "research"

    async def execute(self, task: dict) -> dict[str, Any]:
        topic = task.get("topic", "")
        try:
            answer = await self.ai_router.chat(
                [
                    {
                        "role": "user",
                        "content": f"Research the following topic and summarize the key points concisely:\n\n{topic}",
                    }
                ]
            )
        except AllProvidersFailedError as exc:
            answer = f"Research unavailable — all AI providers failed: {exc}"

        return {"agent": self.name, "topic": topic, "result": answer}
