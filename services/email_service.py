import os
import requests
from dotenv import load_dotenv

load_dotenv()

MAILJET_URL = "https://api.mailjet.com/v3.1/send"


def send_email(to_email: str, subject: str, message: str):
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_API_SECRET")
    sender_email = os.getenv("MAILJET_SENDER_EMAIL")

    if not api_key or not api_secret or not sender_email:
        print("MAILJET credentials are missing.")
        return False, "Missing credentials"

    payload = {
        "Messages": [
            {
                "From": {
                    "Email": sender_email,
                    "Name": "Mock Stream",
                },
                "To": [{"Email": to_email}],
                "Subject": subject,
                "HTMLPart": message,
            }
        ]
    }

    try:
        response = requests.post(
            MAILJET_URL,
            json=payload,
            auth=(api_key, api_secret),
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Success"
        print(f"Email sending failed: {response.status_code} - {response.text}")
        return False, response.text
    except Exception as e:
        print(f"Email sending exception: {str(e)}")
        return False, str(e)


def send_password_reset_code_email(to_email: str, username: str, code: str, expires_minutes: int):
    subject = "MockStream Password Reset Code"
    html = f"""
    <div style=\"font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 16px;\">
      <h2 style=\"margin: 0 0 12px; color: #111827;\">Password Reset</h2>
      <p style=\"color: #374151; line-height: 1.6;\">Hello {username},</p>
      <p style=\"color: #374151; line-height: 1.6;\">
        We received a request to reset your MockStream password. Use the verification code below:
      </p>
      <div style=\"background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 10px; padding: 12px; text-align: center; margin: 18px 0;\">
        <span style=\"font-size: 28px; font-weight: 700; letter-spacing: 6px; color: #3730a3;\">{code}</span>
      </div>
      <p style=\"color: #374151; line-height: 1.6;\">
        This code expires in {expires_minutes} minutes.
      </p>
      <p style=\"color: #6b7280; line-height: 1.6;\">
        If you did not request this, you can safely ignore this email.
      </p>
    </div>
    """
    return send_email(to_email=to_email, subject=subject, message=html)
