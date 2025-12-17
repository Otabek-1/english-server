# services/telegram_bot.py
import requests
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ARCHIVE_CHAT_ID = os.getenv("TELEGRAM_ARCHIVE_CHANNEL")  # yoki -100... ID

def send_audio_zip_to_telegram(zip_path: Path, caption: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(zip_path, "rb") as f:
        resp = requests.post(
            url,
            data={"chat_id": ARCHIVE_CHAT_ID, "caption": caption},
            files={"document": f}
        )
    if not resp.ok:
        print(f"Telegram error: {resp.text}")