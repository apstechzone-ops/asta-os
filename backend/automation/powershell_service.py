import asyncio
from typing import Any


class PowerShellService:
    async def run(self, command: str, timeout: int = 30) -> dict[str, Any]:
        proc = await asyncio.create_subprocess_exec(
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return {"exit_code": -1, "stdout": "", "stderr": "Command timed out"}

        return {
            "exit_code": proc.returncode,
            "stdout": stdout.decode(errors="ignore"),
            "stderr": stderr.decode(errors="ignore"),
        }
