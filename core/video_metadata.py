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
    Supports two formats (priority order):
    1. YYYY-MM-DD$HH-MM-SS-ffffff (standard format)
    2. YYYY-MM-DDTHH-MM-SS (optional -ffffff for microseconds)
    Returns: (iso_timestamp, video_time_HH:MM)
    """
    # Priority 1: standard format - YYYY-MM-DD$HH-MM-SS-ffffff
    m = re.search(r"(\d{4}-\d{2}-\d{2})\$(\d{2}-\d{2}-\d{2}-\d{6})", filename)
    if m:
        date_part = m.group(1)
        time_part = m.group(2)  # HH-MM-SS-ffffff
        # Convert format: 15-45-55-995201 -> 15:45:55.995201
        hh, mm, ss_micro = time_part[:2], time_part[3:5], time_part[6:]
        ss, micro = ss_micro[:2], ss_micro[3:]  # Split SS-ffffff
        iso_ts = f"{date_part}T{hh}:{mm}:{ss}.{micro}"
        video_time = f"{hh}:{mm}"
        return iso_ts, video_time
    
    # Priority 2: T format - YYYY-MM-DDTHH-MM-SS(-ffffff)
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
    
    if duration_seconds is not None:
        end_dt = start_dt + datetime.timedelta(seconds=duration_seconds)
    else:
        # Default to 1 minute if duration unavailable
        end_dt = start_dt + datetime.timedelta(minutes=1)
    
    return end_dt.isoformat()