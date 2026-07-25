from typing import Any

from backend.automation.browser_service import BrowserService
from backend.automation.clipboard_service import ClipboardService
from backend.automation.cmd_service import CmdService
from backend.automation.filesystem_service import FileSystemService
from backend.automation.interface import AutomationInterface
from backend.automation.powershell_service import PowerShellService


class AutomationService(AutomationInterface):
    name = "automation"

    def __init__(self) -> None:
        self.cmd = CmdService()
        self.powershell = PowerShellService()
        self.filesystem = FileSystemService()
        self.clipboard = ClipboardService()
        self.browser = BrowserService()

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"module": self.name, "status": "ok"}

    async def run_command(self, shell: str, command: str, timeout: int = 30) -> dict[str, Any]:
        if shell == "cmd":
            return await self.cmd.run(command, timeout)
        if shell == "powershell":
            return await self.powershell.run(command, timeout)
        raise ValueError(f"Unsupported shell: {shell}")

    async def read_clipboard(self) -> str:
        return await self.clipboard.read()

    async def write_clipboard(self, content: str) -> None:
        await self.clipboard.write(content)
