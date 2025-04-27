import smtplib
from email.mime.text import MIMEText

from .config import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    FROM_EMAIL,
    RECIPIENT_EMAIL
)

def send_notification_email(recipient_email: str, video_name: str, page_url: str) -> None:
    """
    Send a notification email via SMTP using the configured mail service.
    The email subject includes the video name, and the body contains the page URL.
    """
    subject = f"[AVAS] Video Ready: {video_name}"
    body = (
        f"The video has been processed and is now available:\n\n"
        f"Title: {video_name}\n"
        f"Link: {page_url}\n\n"
        "Thank you."
    )

    # Construct the email message
    msg = MIMEText(body, _charset='utf-8')
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = recipient_email

    # Send the email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        # Log in if credentials are provided
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, [recipient_email], msg.as_string())


def notify(video_name: str, page_url: str) -> None:
    """
    Simplified interface: send a notification to the global RECIPIENT_EMAIL.
    """
    send_notification_email(
        recipient_email=RECIPIENT_EMAIL,
        video_name=video_name,
        page_url=page_url
    )



