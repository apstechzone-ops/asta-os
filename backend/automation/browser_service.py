import asyncio
import webbrowser


class BrowserService:
    async def open_url(self, url: str) -> bool:
        return await asyncio.get_event_loop().run_in_executor(None, webbrowser.open, url)
