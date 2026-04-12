import os
import smtplib
from email.mime.text import MIMEText

SMTP_SERVER_URL = os.environ.get("SMTP_SERVER_URL", None)
SMTP_SERVER_PORT = os.environ.get("SMTP_SERVER_PORT", None)
SMTP_SERVER_ID = os.environ.get("SMTP_SERVER_ID", None)
SMTP_SERVER_PASS = os.environ.get("SMTP_SERVER_PASS", None)
if (
    SMTP_SERVER_URL is None
    or SMTP_SERVER_PORT is None
    or SMTP_SERVER_ID is None
    or SMTP_SERVER_PASS is None
):
    raise Exception(
        "[ERROR] Required credentials were not found in the environment variables"
    )


def send_email(
    email_body: str,
    email_to: str,
    email_subject: str,
):
    email = MIMEText(email_body)
    email["To"] = email_to
    email["Subject"] = email_subject
    email["From"] = SMTP_SERVER_ID
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER_URL, SMTP_SERVER_PORT) as smtp_server:
            smtp_server.login(SMTP_SERVER_ID, SMTP_SERVER_PASS)
            smtp_server.sendmail(
                from_addr=SMTP_SERVER_ID, to_addrs=email_to, msg=email.as_string()
            )
    except Exception as e:
        print(f"[ERROR] {e}")
