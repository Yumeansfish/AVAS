import os
from pathlib import Path

# project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

"""
BATCH_INTERVAL represents :
when a video enter in the target folder, it will trigger a timer with BATCH_INTERVAL
all the videos enters in this interval will be recorded 
after the timer finished, they will be handled together
"""
#BTACH_INTERVAL setting
BATCH_INTERVAL = int(os.environ.get("BATCH_INTERVAL", 10))

#AWS setting
AWS_ACCESS_KEY_ID     = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION            = os.environ.get("AWS_REGION", "eu-north-1")
S3_BUCKET_NAME        = os.environ.get("S3_BUCKET_NAME", "")
            
#target folder setting
WATCH_DIR = Path(f"{PROJECT_ROOT.parent}/highlights")
WATCH_DIR.mkdir(parents=True, exist_ok=True)

# survey JSON setting
SURVEY_JSON_PATH = Path(
    os.environ.get(
        "SURVEY_JSON_PATH",
        PROJECT_ROOT / "data" / "surveys" / "questions.json"
    )
)
SURVEY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

# Apps Script URL
SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbylfwlEODbzqq7JKjSoupACf6JBlJthXDyySvryTUpPfj8xbdDSztuNPMzX5_jA7NsR6A/exec"
)

# ─── Google Sheet setting ───
SHEET_ID = os.environ.get("SHEET_ID", "")

# ─── notification setting ───
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "")
SMTP_SERVER     = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT       = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME   = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD   = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL      = os.environ.get("FROM_EMAIL", "")


# ─── survey reminder setting ───
REMINDER_CHECK_HOUR = int(os.environ.get("REMINDER_CHECK_HOUR", "13"))
REMINDER_CHECK_MINUTE = int(os.environ.get("REMINDER_CHECK_MINUTE", "14"))







