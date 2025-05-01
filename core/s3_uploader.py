import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from typing import Optional
from .config import S3_BUCKET_NAME

_s3 = boto3.client("s3")

def upload_to_s3(local_path: str) -> Optional[str]:
    key = os.path.basename(local_path)
    try:
        _s3.upload_file(local_path, S3_BUCKET_NAME, key)
        return key
    except (BotoCoreError, ClientError) as e:
        print(f"❌ fail {e}")
        return None


