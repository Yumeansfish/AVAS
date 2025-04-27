import requests
from .config import SCRIPT_URL, SHEET_ID

def call_appscript(
    video_path: str,
    survey_data: dict,
    video_name: str,
    video_url: str
) -> str | None:
    payload = {
        "videoPath":  video_path,
        "surveyJson": survey_data,
        "videoTitle": video_name,
        "videoUrl":   video_url,
        "sheetId":    SHEET_ID
    }
    try:
        # connect timeout = 5s, read timeout = 30s
        resp = requests.post(SCRIPT_URL, json=payload, timeout=(5, 30))
        resp.raise_for_status()
        return resp.text
    except requests.Timeout:
        print("❌ call Apps Script timeout")
    except requests.RequestException as e:
        print(f"❌ unexpected call Apps Script : {e}")
    return None
