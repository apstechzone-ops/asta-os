from abc import abstractmethod
from typing import Any, Callable, Protocol

from backend.shared import ModuleBase


class Tool(Protocol):
    name: str
    description: str
    parameters_schema: dict[str, Any]

    async def __call__(self, **kwargs: Any) -> Any:
        ...


class ToolManagerInterface(ModuleBase):
    """Registers callable tools and executes them by name.

    The Planner depends only on this interface, never on how a given
    tool is implemented (HTTP call, subprocess, Google API, etc.).
    """

    @abstractmethod
    async def register(self, name: str, description: str, parameters_schema: dict, fn: Callable) -> None:
        ...

    @abstractmethod
    def describe_tools(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def execute(self, name: str, args: dict) -> Any:
        ...
