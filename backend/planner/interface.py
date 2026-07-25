from abc import abstractmethod
from typing import Any, AsyncIterator

from backend.shared import ModuleBase


class PlannerInterface(ModuleBase):
    """Contract for the Planner module.

    Orchestrates intent understanding, memory retrieval, tool execution
    and final response generation. Never imports concrete implementations
    of Memory / RAG / Automation / Agents — only their interfaces.
    """

    @abstractmethod
    async def handle_message(
        self, user_id: str, session_id: str, message: str
    ) -> AsyncIterator[str]:
        """Stream a response for a single user message.

        Yields newline-delimited JSON strings, one event per line:
        - {"type": "action", "status": "executing"|"done"|"failed", "tool": str}
        - {"type": "token", "content": str}
        Implementations must not yield raw, unwrapped text — consumers
        (including the Conversation UI's Current Action indicator) rely
        on this structure to distinguish tool activity from reply content.
        """
        ...

    @abstractmethod
    async def register_tool(self, tool_name: str, tool: Any) -> None:
        ...
