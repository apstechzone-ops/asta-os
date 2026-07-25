from dataclasses import dataclass
from typing import Any, Callable

from backend.tools.interface import ToolManagerInterface


@dataclass
class _RegisteredTool:
    name: str
    description: str
    parameters_schema: dict[str, Any]
    fn: Callable


class ToolManager(ToolManagerInterface):
    name = "tool_manager"

    def __init__(self) -> None:
        self._tools: dict[str, _RegisteredTool] = {}

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        self._tools.clear()

    def health(self) -> dict:
        return {"module": self.name, "status": "ok", "registered": list(self._tools.keys())}

    async def register(self, name: str, description: str, parameters_schema: dict, fn: Callable) -> None:
        self._tools[name] = _RegisteredTool(name, description, parameters_schema, fn)

    def describe_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters_schema}
            for t in self._tools.values()
        ]

    async def execute(self, name: str, args: dict) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Unknown tool: {name}")
        result = tool.fn(**args)
        if hasattr(result, "__await__"):
            result = await result
        return result


_tool_manager_singleton: ToolManager | None = None


def get_tool_manager() -> ToolManager:
    global _tool_manager_singleton
    if _tool_manager_singleton is None:
        _tool_manager_singleton = ToolManager()
    return _tool_manager_singleton
