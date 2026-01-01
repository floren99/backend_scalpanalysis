import smtplib
import os
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM")

def send_reset_email(to_email: str, code: str):
    msg = EmailMessage()
    msg["Subject"] = "Reset Password"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.set_content(f"Kode reset password kamu: {code}")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
