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


#target folder setting
WATCH_DIR = Path(
    os.environ.get(
        "WATCH_DIR",
        PROJECT_ROOT / "data" / "video"
    )
)
WATCH_DIR.mkdir(parents=True, exist_ok=True)

# survey JSON setting
SURVEY_JSON_PATH = Path(
    os.environ.get(
        "SURVEY_JSON_PATH",
        PROJECT_ROOT / "data" / "surveys" / "questions.json"
    )
)
SURVEY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

# Google Sheet setting
SHEET_ID = "1X8YgETui7itJbCxwiRsiiT1ALqtGUV6ntaJAKQpmgxM"

# Apps Script URL
SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbyZEIkS4lqcxfLhABVDsBInSO6gCqFtP7niVV3QoTmeADPHIw9PVd6pKWpybQEdfCxw/exec"
)

# Amazon S3 setting
S3_BUCKET_NAME = "avas"

# notification setting
RECIPIENT_EMAIL = "yuchengyu0507@outlook.com"
SMTP_SERVER    = "smtp.gmail.com"
SMTP_PORT      = 587
SMTP_USERNAME  = "nightnight2024@gmail.com"
SMTP_PASSWORD  = "cjxa vnlh uhyo hfmg"
FROM_EMAIL     = "nightnight2024+no-reply@gmail.com"







