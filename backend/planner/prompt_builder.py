from typing import Any

from backend.memory.interface import MemoryInterface
from backend.rag.interface import RAGInterface


class PromptBuilder:
    """Owns context assembly. This is the one place conversation history,
    long-term memory, and RAG context get combined into what a provider
    actually sees — providers never perform retrieval themselves, and
    nothing outside this class should be building prompt strings by hand.
    """

    MEMORY_TOP_K = 3
    RAG_TOP_K = 3

    def __init__(self, memory: MemoryInterface, rag: RAGInterface | None = None) -> None:
        self.memory = memory
        self.rag = rag  # optional: Planner can run without a knowledge base wired in

    @staticmethod
    def format_history(messages: list[dict[str, Any]], limit: int = 10) -> str:
        if not messages:
            return "(no prior messages)"
        return "\n".join(f"{m['role']}: {m['content']}" for m in messages[-limit:])

    async def _fetch_memories(self, user_id: str, message: str) -> str:
        try:
            results = await self.memory.search_vector(
                message, top_k=self.MEMORY_TOP_K, filters={"user_id": user_id}
            )
        except Exception:
            return ""  # vector store unreachable — degrade gracefully, don't break the chat
        if not results:
            return ""
        return "\n".join(f"- {r['content']}" for r in results)

    async def _fetch_rag_context(self, message: str) -> str:
        if self.rag is None:
            return ""
        try:
            results = await self.rag.retrieve(message, top_k=self.RAG_TOP_K)
        except Exception:
            return ""
        if not results:
            return ""
        return "\n".join(f"- {r['content']}" for r in results)

    async def build(
        self,
        *,
        system_prompt: str,
        user_id: str,
        message: str,
        history: list[dict[str, Any]],
        tool_context: str = "",
    ) -> list[dict[str, str]]:
        """Returns an OpenAI-style messages array ready to hand to AIRouter."""
        memories_block = await self._fetch_memories(user_id, message)
        rag_block = await self._fetch_rag_context(message)
        history_block = self.format_history(history)

        parts: list[str] = []
        if memories_block:
            parts.append(f"Relevant memories about this user:\n{memories_block}")
        if rag_block:
            parts.append(f"Relevant knowledge base context:\n{rag_block}")
        parts.append(f"Conversation so far:\n{history_block}")
        parts.append(f"User: {message}")
        if tool_context:
            parts.append(tool_context.strip())
        parts.append("Respond helpfully and concisely.")

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n\n".join(parts)},
        ]
