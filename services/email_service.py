import os
import dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
dotenv.load_dotenv()
def send_email(to_email, subject, message):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(message, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login(sender_email,sender_password)

        server.sendmail(sender_email,to_email,msg.as_string())
        server.quit()
        print("Email sent!")

    except Exception as e:
        print(f"Error: {e}")
    