import requests
from typing import Optional, List
from .config import SCRIPT_URL, SHEET_ID

def call_appscript(
    video_path: str,
    survey_data: dict,
    video_name: str,
    video_url: str
) -> Optional[str]:
    return call_appscript_batch(
        video_paths  = [video_path],
        video_names  = [video_name],
        video_urls   = [video_url],
        video_times  = [],           
        survey_data  = survey_data
    )

def call_appscript_batch(
    video_paths: List[str],
    video_names: List[str],
    video_urls:  List[str],
    video_times: List[str],
    survey_data: dict
) -> Optional[str]:
    payload = {
        "videoPaths":  video_paths,
        "videoNames":  video_names,
        "videoUrls":   video_urls,
        "videoTimes":  video_times,
        "surveyJson":  survey_data,
        "sheetId":     SHEET_ID
    }
    try:
        resp = requests.post(SCRIPT_URL, json=payload, timeout=(5, 30))
        resp.raise_for_status()
        return resp.text
    except requests.Timeout:
        print("❌ call Apps Script batch timeout")
    except requests.RequestException as e:
        print(f"❌ unexpected call Apps Script batch: {e}")
    return None






