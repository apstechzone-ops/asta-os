import asyncio
from typing import AsyncIterator

from backend.config import get_settings
from backend.logging_ import get_logger

logger = get_logger(__name__)

_CHUNK_SIZE = 4096


class PiperTTS:
    def __init__(self) -> None:
        settings = get_settings()
        self.binary_path = settings.PIPER_BINARY_PATH
        self.model_path = settings.PIPER_MODEL_PATH

    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        proc = await asyncio.create_subprocess_exec(
            self.binary_path,
            "--model",
            self.model_path,
            "--output-raw",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        assert proc.stdin is not None and proc.stdout is not None
        proc.stdin.write(text.encode("utf-8"))
        await proc.stdin.drain()
        proc.stdin.close()

        try:
            while True:
                chunk = await proc.stdout.read(_CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk
        finally:
            await proc.wait()
            if proc.returncode not in (0, None):
                stderr = await proc.stderr.read() if proc.stderr else b""
                logger.error("Piper TTS exited with %s: %s", proc.returncode, stderr.decode(errors="ignore"))
