import os
import subprocess
from typing import Optional, Tuple
from .config import S3_BUCKET_NAME
import boto3
from botocore.exceptions import BotoCoreError, ClientError


def convert_to_mp4(video_path: str) -> Tuple[str, bool]:
    """
    Convert video to MP4 format if needed.
    Returns: (output_path, should_skip)
    """
    ext = os.path.splitext(video_path)[1].lower()
    
    if ext == ".mp4":
        return video_path, False
    
    mp4_path = os.path.splitext(video_path)[0] + ".mp4"
    
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-movflags",
                "+faststart",
                mp4_path,
            ],
            check=True,
        )
        return mp4_path, True
    except subprocess.CalledProcessError:
        # Return original path if conversion fails
        return video_path, False

_s3 = boto3.client("s3")
def upload_to_s3(local_path: str) -> Optional[str]:
    key = os.path.basename(local_path)
    try:
        _s3.upload_file(local_path, S3_BUCKET_NAME, key)
        return key
    except (BotoCoreError, ClientError) as e:
        print(f"❌ fail {e}")
        return None

def process_and_upload_video(video_path: str) -> Optional[str]:
    """
    Process video (convert if needed) and upload to S3.
    Returns S3 URL if successful, None otherwise.
    """
    upload_path, _ = convert_to_mp4(video_path)
    
    s3_key = upload_to_s3(upload_path)
    if not s3_key:
        return None
    
    return f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"