import os
import smtplib
from email.message import EmailMessage


def send_reset_email(to_email: str, code: str):
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")

    if not email_user or not email_pass:
        raise RuntimeError("EMAIL_USER atau EMAIL_PASS tidak terbaca dari environment")

    msg = EmailMessage()
    msg["Subject"] = "Permintaan Reset Password Apk Analisis Masalah Kulit Kepala"
    msg["From"] = email_user
    msg["To"] = to_email
    msg.set_content(
        f"""Halo Sobat Pengguna Analisis Masalah Kulit Kepala,

Kami menerima permintaan untuk melakukan reset password pada akun Anda.

Kode reset password:
{code}

Silakan masukkan kode tersebut pada aplikasi untuk melanjutkan proses reset password.

Apabila Anda tidak merasa melakukan permintaan ini, Anda dapat mengabaikan email ini dengan aman.

Terima kasih atas kepercayaan Anda menggunakan layanan kami.

Hormat,
Owner Apk Analisis Kulit Kepala
"""
    )

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(email_user, email_pass)
    server.send_message(msg)
    server.quit()
