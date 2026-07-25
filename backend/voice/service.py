from typing import AsyncIterator

from backend.voice.interface import VoiceInterface
from backend.voice.piper_tts import PiperTTS
from backend.voice.whisper_stt import WhisperSTT


class VoiceService(VoiceInterface):
    name = "voice"

    def __init__(self) -> None:
        self.stt = WhisperSTT()
        self.tts = PiperTTS()

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"module": self.name, "status": "ok"}

    async def transcribe_stream(self, audio_chunks: AsyncIterator[bytes]) -> AsyncIterator[str]:
        async for text in self.stt.transcribe_stream(audio_chunks):
            yield text

    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        async for chunk in self.tts.synthesize(text):
            yield chunk
