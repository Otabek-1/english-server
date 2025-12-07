import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_email(to_email: str, subject: str, message: str):
    api_key = "a465a0473f0751ef239d896315ccb0a4"
    api_secret = "5873ed096370a6089c4829ee5399f63c"
    sender_email = "burhonovotabek5@gmail.com"

    if not api_key or not api_secret or not sender_email:
        print("❌ MAILJET API KEY yoki SECRET yoki SENDER_EMAIL yo'q!")
        return False, "Missing credentials"

    url = "https://api.mailjet.com/v3.1/send"

    payload = {
        "Messages": [
            {
                "From": {
                    "Email": sender_email,
                    "Name": "Mock Stream"
                },
                "To": [
                    {"Email": to_email}
                ],
                "Subject": subject,
                "HTMLPart": message
            }
        ]
    }

    try:
        response = requests.post(
            url,
            json=payload,
            auth=(api_key, api_secret),  # Mailjet basic auth
            timeout=10
        )

        if response.status_code == 200:
            print(f"✅ Email {to_email} ga muvaffaqiyatli jo'natildi!")
            return True, "Success"
        else:
            print(f"❌ Xato: {response.text}")
            return False, response.text

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False, str(e)
