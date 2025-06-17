import os
import re
import datetime
import subprocess
from typing import Optional, Tuple


import re
from typing import Optional, Tuple

def extract_timestamp_from_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract timestamp from video filename.
    Supports two formats:
      1. YYYY-MM-DD$HH-MM-SS-ffffff
      2. YYYY-MM-DDTHH-MM-SS (optional -ffffff for microseconds)
    Returns: (iso_timestamp, video_time_HH:MM)
    """
    m = re.search(
        r"(?P<date>\d{4}-\d{2}-\d{2})T(?P<time>\d{2}-\d{2}-\d{2})(?:-(?P<micro>\d{1,6}))?",
        filename
    )
    if m:
        date_part = m.group("date")
        hh, mm, ss = m.group("time").split("-")
        micro = (m.group("micro") or "0").ljust(6, "0")
        iso_ts = f"{date_part}T{hh}:{mm}:{ss}.{micro}"
        video_time = f"{hh}:{mm}"
        return iso_ts, video_time
    
    m = re.search(r"(\d{4}-\d{2}-\d{2})\$(\d{2}-\d{2}-\d{2})-(\d{6})", filename)
    if m:
        date_part, time_part, micro = m.group(1), m.group(2), m.group(3)
        hh, mm, ss = time_part.split("-")
        iso_ts = f"{date_part}T{hh}:{mm}:{ss}.{micro}"
        video_time = f"{hh}:{mm}"
        return iso_ts, video_time

    return None, None



def get_fallback_timestamp(path: str) -> str:
    """Get timestamp from file modification time."""
    ts = os.path.getmtime(path)
    return datetime.datetime.fromtimestamp(ts).isoformat()


def get_video_duration(video_path: str) -> Optional[float]:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", 
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return None


def calculate_end_time(iso_timestamp: str, duration_seconds: Optional[float]) -> str:
    """Calculate video end time based on start time and duration."""
    start_dt = datetime.datetime.fromisoformat(iso_timestamp)
    
    if duration_seconds:
        end_dt = start_dt + datetime.timedelta(seconds=duration_seconds)
    else:
        # Default to 1 minute if duration unavailable
        end_dt = start_dt + datetime.timedelta(minutes=1)
    
    return end_dt.isoformat()