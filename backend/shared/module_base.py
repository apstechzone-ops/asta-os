from abc import ABC, abstractmethod


class ModuleBase(ABC):
    """Base contract every backend module implements.

    Enforces lifecycle hooks so the Planner / Agent Manager can manage
    modules without depending on their concrete implementations.
    """

    name: str

    @abstractmethod
    async def startup(self) -> None:
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        ...

    @abstractmethod
    def health(self) -> dict:
        ...
