import asyncio
import tempfile
from typing import AsyncIterator

try:
    from faster_whisper import WhisperModel
except ImportError:
    _model = None

from backend.config import get_settings
from backend.logging_ import get_logger

logger = get_logger(__name__)


class WhisperSTT:
    _model: WhisperModel | None = None

    def __init__(self) -> None:
        settings = get_settings()
        self.model_size = settings.WHISPER_MODEL_SIZE
        self.device = settings.WHISPER_DEVICE
        self.compute_type = settings.WHISPER_COMPUTE_TYPE

    def _get_model(self):
        if WhisperModel is None:
            raise RuntimeError("faster-whisper is not installed.")

        if WhisperSTT._model is None:
         WhisperSTT._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )

        return WhisperSTT._model

    async def transcribe_stream(self, audio_chunks: AsyncIterator[bytes]) -> AsyncIterator[str]:
        """Buffers incoming audio into a temp file, transcribes once the
        stream ends. Real-time partials would require a streaming ASR
        backend (e.g. whisper.cpp with VAD chunking) — left as a future
        enhancement; this yields the final transcript as a single chunk.
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            path = tmp.name
            async for chunk in audio_chunks:
                tmp.write(chunk)

        loop = asyncio.get_event_loop()
        segments, _info = await loop.run_in_executor(
            None, lambda: self._get_model().transcribe(path, beam_size=5)
        )
        for segment in segments:
            yield segment.text.strip()

    async def transcribe_file(self, path: str) -> str:
        loop = asyncio.get_event_loop()
        segments, _info = await loop.run_in_executor(
            None, lambda: self._get_model().transcribe(path, beam_size=5)
        )
        return " ".join(s.text.strip() for s in segments)
