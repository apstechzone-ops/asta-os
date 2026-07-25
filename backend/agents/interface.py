from abc import abstractmethod
from typing import Any

from backend.shared import ModuleBase


class AgentInterface(ModuleBase):
    """Contract every future agent (Research, Coding, Google, Finance,
    Browser, Memory, Learning, Automation) must implement."""

    @abstractmethod
    async def can_handle(self, task: dict) -> bool:
        ...

    @abstractmethod
    async def execute(self, task: dict) -> dict[str, Any]:
        ...


class AgentManagerInterface(ModuleBase):
    """Registers agents and routes tasks to the correct one."""

    @abstractmethod
    async def register_agent(self, agent: AgentInterface) -> None:
        ...

    @abstractmethod
    async def dispatch(self, task: dict) -> dict[str, Any]:
        ...
