from gtts import gTTS
from io import BytesIO

def TTS(text: str) -> BytesIO:
    mp3_fp = BytesIO()
    gTTS(text=text, lang="en").write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp
