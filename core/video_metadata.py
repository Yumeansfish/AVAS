import os
import re
import datetime
import subprocess
from typing import Optional, Tuple


def extract_timestamp_from_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract timestamp from video filename.
    Returns: (iso_timestamp, video_time_HH:MM)
    """
    timestamp_match = re.search(
        r"(\d{4}-\d{2}-\d{2})\$(\d{2}-\d{2}-\d{2}-\d{6})", filename
    )
    
    if timestamp_match:
        date_part = timestamp_match.group(1)
        time_part = timestamp_match.group(2)
        
        # Convert format: 15-45-55-995201 -> 15:45:55.995201
        time_formatted = (
            time_part[:2]
            + ":"
            + time_part[3:5]
            + ":"
            + time_part[6:8]
            + "."
            + time_part[9:]
        )
        iso_ts = f"{date_part}T{time_formatted}"
        video_time = time_part[:2] + ":" + time_part[3:5]
        
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