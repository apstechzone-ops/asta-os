from abc import abstractmethod
from typing import AsyncIterator

from backend.shared import ModuleBase


class VoiceInterface(ModuleBase):
    """Contract for Voice module: STT (Whisper) and TTS (Piper)."""

    @abstractmethod
    async def transcribe_stream(self, audio_chunks: AsyncIterator[bytes]) -> AsyncIterator[str]:
        ...

    @abstractmethod
    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        ...
