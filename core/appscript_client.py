import requests
from typing import Optional, List
from .config import (
    SCRIPT_URL,
    SHEET_ID,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    S3_BUCKET_NAME
)

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
    """
    call the appscript to generate the pages

    input:
        video_paths (List[str]): List of local file paths for each video
        video_names (List[str]): List of the video file names 
        video_urls (List[str]): List of Amazon S3 links for each video
        video_times (List[str]): List of ISO timestamps for each video
        survey_data (dict): survey JSON to embed in the page

    output:
        Optional[str]: The generated page URL, or None on failure.
    """
    payload = {
        "videoPaths":   video_paths,
        "videoNames":   video_names,
        "videoUrls":    video_urls,
        "videoTimes":   video_times,
        "surveyJson":   survey_data,
        
        "sheetId":       SHEET_ID,
        "awsAccessKey":  AWS_ACCESS_KEY_ID,
        "awsSecretKey":  AWS_SECRET_ACCESS_KEY,
        "awsRegion":     AWS_REGION,
        "s3Bucket":      S3_BUCKET_NAME
    }

    try:
        resp = requests.post(SCRIPT_URL, json=payload, timeout=(5, 30))
        resp.raise_for_status()
        return resp.text.strip()
    except requests.Timeout:
        print("❌ call Apps Script batch timeout")
    except requests.RequestException as e:
        print(f"❌ unexpected call Apps Script batch: {e}")
    return None







