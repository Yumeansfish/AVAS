import os
from pathlib import Path

# project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# survey JSON path 
SURVEY_JSON_PATH = Path(
    os.environ.get(
        "SURVEY_JSON_PATH",
        PROJECT_ROOT / "data" / "surveys" / "questions.json"
    )
)
SURVEY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

# Google Sheet ID
SHEET_ID = "1X8YgETui7itJbCxwiRsiiT1ALqtGUV6ntaJAKQpmgxM"

# Apps Script URL
SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbwfcEtuEyflhG57IE_rSb1QAz0Dhx-RCFvHVw7qwXbt2GKxJuzqeXb7ru2wNlgvMJEg/exec"
)

# Amazon S3
S3_BUCKET_NAME = "avas"

# SMTP (Gmail)
RECIPIENT_EMAIL = "yuchengyu0507@outlook.com"
SMTP_SERVER    = "smtp.gmail.com"
SMTP_PORT      = 587
SMTP_USERNAME  = "nightnight2024@gmail.com"
SMTP_PASSWORD  = "cjxa vnlh uhyo hfmg"
FROM_EMAIL     = "nightnight2024+no-reply@gmail.com"







