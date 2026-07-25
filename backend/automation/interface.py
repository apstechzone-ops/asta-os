from abc import abstractmethod
from typing import Any

from backend.shared import ModuleBase


class AutomationInterface(ModuleBase):
    """Contract for Windows Automation module: CMD, PowerShell,
    File System, Browser, Clipboard — each a decoupled sub-service."""

    @abstractmethod
    async def run_command(self, shell: str, command: str, timeout: int = 30) -> dict[str, Any]:
        ...

    @abstractmethod
    async def read_clipboard(self) -> str:
        ...

    @abstractmethod
    async def write_clipboard(self, content: str) -> None:
        ...
