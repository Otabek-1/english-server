# services/telegram_bot.py
import os

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ARCHIVE_CHAT_ID = os.getenv("TELEGRAM_ARCHIVE_CHANNEL")


def send_document_to_telegram(
    file_buffer,
    filename: str,
    caption: str,
    mime_type: str = "application/octet-stream",
    chat_id: str | None = None,
) -> bool:
    """
    Send a file to Telegram archive channel.
    Returns True on success, False otherwise.
    """
    target_chat_id = chat_id or ARCHIVE_CHAT_ID
    if not BOT_TOKEN:
        print("Telegram error: TELEGRAM_BOT_TOKEN is not configured")
        return False
    if not target_chat_id:
        print("Telegram error: target chat id is not configured")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    file_buffer.seek(0)

    files = {"document": (filename, file_buffer, mime_type)}
    data = {"chat_id": target_chat_id, "caption": caption}

    try:
        resp = requests.post(url, data=data, files=files, timeout=60)
    except Exception as exc:
        print("Telegram request error:", exc)
        return False

    if not resp.ok:
        print("Telegram error:", resp.text)
        return False

    return True


def send_audio_zip_to_telegram(zip_buffer, caption: str, chat_id: str | None = None) -> bool:
    return send_document_to_telegram(
        file_buffer=zip_buffer,
        filename="speaking_audios.zip",
        caption=caption,
        mime_type="application/zip",
        chat_id=chat_id,
    )
