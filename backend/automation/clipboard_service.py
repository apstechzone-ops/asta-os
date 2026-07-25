import asyncio

import pyperclip


class ClipboardService:
    async def read(self) -> str:
        return await asyncio.get_event_loop().run_in_executor(None, pyperclip.paste)

    async def write(self, content: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, pyperclip.copy, content)
