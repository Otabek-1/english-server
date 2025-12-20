from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from services.tts_service import TTS
from io import BytesIO
import zipfile

router = APIRouter(prefix="/tts", tags=["TTS"])

@router.post("/audio")
def audio(data: dict):
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for key, text in data.items():
            audio_fp = TTS(text)
            zipf.writestr(f"{key}.mp3", audio_fp.getvalue())

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=audios.zip"}
    )
