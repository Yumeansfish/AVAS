import smtplib
from email.mime.text import MIMEText
from typing import List

from .config import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    FROM_EMAIL,
    RECIPIENT_EMAIL
)

def send_notification_email(recipient_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body, _charset='utf-8')
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = recipient_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, [recipient_email], msg.as_string())

def notify(video_name: str, page_url: str) -> None:
    subject = f"[AVAS] Video Ready: {video_name}"
    body = (
        f"The video has been processed and is now available:\n\n"
        f"Title: {video_name}\n"
        f"Link: {page_url}\n\n"
        "Thank you."
    )
    send_notification_email(RECIPIENT_EMAIL, subject, body)

def notify_batch(video_names: List[str], video_urls: List[str]) -> None:
    subject = "[AVAS] Batch Video Upload Complete"
    # wrap each URL in <…> 
    lines = [f"{name}: <{url}>" for name, url in zip(video_names, video_urls)]
    body = "The following videos have been processed and are available:\n\n" + "\n".join(lines)
    send_notification_email(RECIPIENT_EMAIL, subject, body)
    print(body)





