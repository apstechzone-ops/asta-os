import json
from typing import Any, AsyncIterator

from backend.ai_providers import AIRouter, AllProvidersFailedError, UsageLogCallback, get_ai_router
from backend.memory.conversation_manager import ConversationManager
from backend.memory.interface import MemoryInterface
from backend.planner.interface import PlannerInterface
from backend.planner.prompt_builder import PromptBuilder
from backend.rag.interface import RAGInterface
from backend.tools.interface import ToolManagerInterface

SYSTEM_PROMPT = """
You are Asta OS, an advanced AI operating system assistant.

Your name is Asta.

You are the intelligence layer of Asta OS. You help users by:
- answering questions
- reasoning through problems
- planning tasks
- using tools when available
- using memory and knowledge when provided

Important rules:
- Always identify yourself as Asta OS.
- Do not say you are just an AI language model.
- Do not deny being Asta.
- Be helpful, concise, and intelligent.
- If you do not know something, say you do not know.

You are powered by an AI model, but the Asta OS system controls your memory,
tools, conversation history, and knowledge.
"""

DECISION_USER_TEMPLATE = """Conversation so far:
{history}

Available tools:
{tools}

User: {message}

If a tool must be called to answer, respond with ONLY:
TOOL_CALL: {{"tool": "<tool_name>", "args": {{...}}}}

Otherwise respond with ONLY:
NO_TOOL
"""


class PlannerService(PlannerInterface):
    name = "planner"

    def __init__(
        self,
        memory: MemoryInterface,
        tool_manager: ToolManagerInterface,
        ai_router: AIRouter | None = None,
        rag: RAGInterface | None = None,
        usage_logger: UsageLogCallback | None = None,
    ) -> None:
        self.memory = memory
        self.tool_manager = tool_manager
        self.ai_router = ai_router or get_ai_router()
        self.conversation_manager = ConversationManager(memory=memory)
        self.prompt_builder = PromptBuilder(memory=memory, rag=rag)
        self.usage_logger = usage_logger

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {
            "module": self.name,
            "status": "ok",
            "providers": self.ai_router.configured_providers(),
            "rag_connected": self.prompt_builder.rag is not None,
        }

    async def register_tool(self, tool_name: str, tool: Any) -> None:
        await self.tool_manager.register(
            name=tool_name,
            description=getattr(tool, "description", ""),
            parameters_schema=getattr(tool, "parameters_schema", {}),
            fn=tool,
        )

    async def _decide_tool(self, history: str, tools_desc: str, message: str) -> dict | None:
        if not tools_desc.strip():
            return None

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": DECISION_USER_TEMPLATE.format(history=history, tools=tools_desc, message=message),
            },
        ]
        try:
            decision = await self.ai_router.chat(messages)
        except AllProvidersFailedError:
            return None  # tool-call decision is best-effort; fall through to a plain reply

        decision = decision.strip()
        if decision.startswith("TOOL_CALL:"):
            try:
                return json.loads(decision[len("TOOL_CALL:"):].strip())
            except json.JSONDecodeError:
                return None
        return None

    async def handle_message(
        self, user_id: str, session_id: str, message: str
    ) -> AsyncIterator[str]:
        """Yields newline-delimited JSON strings, one event per line:
        - {"type": "action", "status": "executing"|"done"|"failed", "tool": "<name>"}
        - {"type": "token", "content": "<chunk>"}
        - {"type": "error", "message": "<text>"} — emitted if every configured
          AI provider failed; the frontend should show this rather than hang.
        """
        await self.conversation_manager.save_message(session_id, "user", message, user_id=user_id)
        history_msgs = await self.conversation_manager.trim_history(session_id, limit=50)
        history = PromptBuilder.format_history(history_msgs)

        tools_desc = "\n".join(
            f"- {t['name']}: {t['description']}" for t in self.tool_manager.describe_tools()
        )

        tool_context = ""
        tool_call = await self._decide_tool(history, tools_desc, message)
        if tool_call and tool_call.get("tool"):
            tool_name = tool_call["tool"]
            yield json.dumps({"type": "action", "status": "executing", "tool": tool_name}) + "\n"
            try:
                result = await self.tool_manager.execute(tool_name, tool_call.get("args", {}))
                tool_context = f"Tool `{tool_name}` returned: {result}"
                yield json.dumps({"type": "action", "status": "done", "tool": tool_name}) + "\n"
            except Exception as exc:  # tool failure should not crash the conversation
                tool_context = f"Tool `{tool_name}` failed: {exc}"
                yield json.dumps({"type": "action", "status": "failed", "tool": tool_name}) + "\n"

        # Context assembly (system prompt + relevant long-term memories + RAG
        # context + conversation history + current message) happens entirely
        # in PromptBuilder — this is the only place that talks to it.
        messages = await self.prompt_builder.build(
            system_prompt=SYSTEM_PROMPT,
            user_id=user_id,
            message=message,
            history=history_msgs,
            tool_context=tool_context,
        )

        full_response = ""
        task_type = self.ai_router.classify_task(message)
        try:
            async for token in self.ai_router.stream(
                messages,
                task_type=task_type,
                on_log=self.usage_logger,
                session_id=session_id,
                user_id=user_id,
            ):
                full_response += token
                yield json.dumps({"type": "token", "content": token}) + "\n"
        except AllProvidersFailedError:
            yield json.dumps(
                {"type": "error", "message": "All configured AI providers are currently unreachable."}
            ) + "\n"

        if full_response:
            await self.conversation_manager.save_message(session_id, "assistant", full_response, user_id=user_id)
