import os
import dotenv
import requests
from typing import Tuple

dotenv.load_dotenv()

def send_email(to_email: str, subject: str, message: str) -> Tuple[bool, str]:
    """
    Resend.com orqali email jo'natish
    Render.com da ishlaydi va bloklanmaydi
    """
    api_key = os.getenv("RESEND_API_KEY")
    sender_email = os.getenv("SENDER_EMAIL")
    
    if not api_key or not sender_email:
        error_msg = "❌ RESEND_API_KEY yoki SENDER_EMAIL .env da yo'q!"
        print(error_msg)
        return False, error_msg
    
    url = "https://api.resend.com/emails"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": sender_email,
        "to": to_email,
        "subject": subject,
        "html": message
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Email {to_email} ga jo'natildi! (ID: {response.json().get('id')})")
            return True, "Email sent successfully"
        else:
            error_msg = f"❌ Resend xatosi: {response.json().get('message', response.text)}"
            print(error_msg)
            return False, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = "❌ Request vaqti o'tib ketdi"
        print(error_msg)
        return False, error_msg
    except requests.exceptions.ConnectionError:
        error_msg = "❌ Internet ulanishida xato"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"❌ Xato: {str(e)}"
        print(error_msg)
        return False, error_msg