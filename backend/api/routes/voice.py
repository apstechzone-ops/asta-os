import tempfile

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.voice.service import VoiceService

router = APIRouter(prefix="/voice", tags=["voice"])


def get_voice_service() -> VoiceService:
    return VoiceService()


class SynthesizeRequest(BaseModel):
    text: str


@router.post("/transcribe")
async def transcribe(
    file: UploadFile,
    voice: VoiceService = Depends(get_voice_service),
    _current_user: dict = Depends(get_current_user),
):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        path = tmp.name

    text = await voice.stt.transcribe_file(path)
    return {"text": text}


@router.post("/synthesize")
async def synthesize(
    payload: SynthesizeRequest,
    voice: VoiceService = Depends(get_voice_service),
    _current_user: dict = Depends(get_current_user),
):
    async def stream():
        async for chunk in voice.synthesize(payload.text):
            yield chunk

    return StreamingResponse(stream(), media_type="audio/x-raw")
