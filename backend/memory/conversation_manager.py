from typing import Any

from backend.memory.interface import MemoryInterface


class ConversationManager:
    """Orchestration layer over MemoryInterface for conversation-specific
    operations. save_message/load_history/summarize are thin delegations —
    MemoryInterface already owns that storage logic, this does not duplicate it.

    trim_history is the one genuinely new capability: as a conversation grows,
    raw message history eventually exceeds what's reasonable to hand a provider
    on every turn. Instead of a hard count-based cutoff, this falls back to the
    stored (or freshly generated) summary for everything except the last few
    messages, once the raw history crosses a character budget.
    """

    def __init__(self, memory: MemoryInterface, max_history_chars: int = 4000, keep_recent: int = 4) -> None:
        self.memory = memory
        self.max_history_chars = max_history_chars
        self.keep_recent = keep_recent

    async def save_message(self, session_id: str, role: str, content: str, user_id: str | None = None) -> None:
        await self.memory.add_short_term(session_id, role, content, user_id)

    async def load_history(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return await self.memory.get_recent_messages(session_id, limit)

    async def summarize(self, session_id: str) -> str:
        return await self.memory.summarize_session(session_id)

    async def trim_history(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Returns a context-window-safe history: unchanged if it already
        fits max_history_chars, otherwise the last `keep_recent` messages
        verbatim plus a summary standing in for everything older."""
        messages = await self.memory.get_recent_messages(session_id, limit)

        total_chars = sum(len(m.get("content", "")) for m in messages)
        if total_chars <= self.max_history_chars or len(messages) <= self.keep_recent:
            return messages

        recent = messages[-self.keep_recent:]
        summary = await self.memory.summarize_session(session_id)

        trimmed: list[dict[str, Any]] = []
        if summary:
            trimmed.append({"role": "system", "content": f"[Earlier conversation summary]: {summary}"})
        trimmed.extend(recent)
        return trimmed
