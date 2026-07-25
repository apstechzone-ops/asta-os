import asyncio
from pathlib import Path
from typing import Any


class FileSystemService:
    async def list_dir(self, path: str) -> list[dict[str, Any]]:
        def _list() -> list[dict[str, Any]]:
            p = Path(path)
            return [
                {"name": entry.name, "is_dir": entry.is_dir(), "size": entry.stat().st_size}
                for entry in p.iterdir()
            ]

        return await asyncio.get_event_loop().run_in_executor(None, _list)

    async def read_file(self, path: str, max_bytes: int = 200_000) -> str:
        def _read() -> str:
            return Path(path).read_text(encoding="utf-8", errors="ignore")[:max_bytes]

        return await asyncio.get_event_loop().run_in_executor(None, _read)

    async def write_file(self, path: str, content: str) -> None:
        def _write() -> None:
            Path(path).write_text(content, encoding="utf-8")

        await asyncio.get_event_loop().run_in_executor(None, _write)

    async def delete(self, path: str) -> None:
        def _delete() -> None:
            p = Path(path)
            if p.is_dir():
                p.rmdir()
            else:
                p.unlink(missing_ok=True)

        await asyncio.get_event_loop().run_in_executor(None, _delete)
