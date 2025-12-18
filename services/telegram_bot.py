# services/telegram_bot.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ARCHIVE_CHAT_ID = os.getenv("TELEGRAM_ARCHIVE_CHANNEL")

def send_audio_zip_to_telegram(zip_buffer, caption: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

    zip_buffer.seek(0)  # MUHIM

    files = {
        "document": ("speaking_audios.zip", zip_buffer, "application/zip")
    }

    data = {
        "chat_id": ARCHIVE_CHAT_ID,
        "caption": caption
    }

    resp = requests.post(url, data=data, files=files)

    if not resp.ok:
        print("Telegram error:", resp.text)
