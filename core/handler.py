import os
import json
import subprocess
from watchdog.events import FileSystemEventHandler

from .s3_uploader import upload_to_s3
from .appscript_client import call_appscript
from .notifier import notify
from .config import SURVEY_JSON_PATH, S3_BUCKET_NAME

class VideoHandler(FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        # skip new mp4
        self._skip = set()

    def on_created(self, event):
        if event.is_directory:
            return

        path = event.src_path
        if path in self._skip:
            self._skip.remove(path)
            return

        ext = os.path.splitext(path)[1].lower()
        # mov/avi/mp4
        if ext not in ('.mov', '.avi', '.mp4'):
            return

        video_name = os.path.basename(path)
        print(f"new video: {video_name}")

        # 1. read survey
        survey_data = {}
        if os.path.exists(SURVEY_JSON_PATH):
            try:
                with open(SURVEY_JSON_PATH, 'r', encoding='utf-8') as f:
                    survey_data = json.load(f)
            except Exception as e:
                print(f"fail on reading survey: {e}")
        else:
            print("no survey")

        # 2. turn to .mp4 to show it in any browser
        if ext != '.mp4':
            base = os.path.splitext(path)[0]
            mp4_path = base + ".mp4"
            # avoid reapeat deal with .mp4
            self._skip.add(mp4_path)
            try:
                print(f"convert to MP4: {mp4_path}")
                subprocess.run([
                    "ffmpeg", "-i", path,
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-movflags", "+faststart",
                    mp4_path
                ], check=True)
                print(f"✅ converting finished: {mp4_path}")
                upload_path = mp4_path
            except Exception as e:
                print(f"❌ fail in converting to mp4 ({e})，")
                upload_path = path
        else:
            upload_path = path

        # 3. upload to S3
        s3_key = upload_to_s3(upload_path)
        if not s3_key:
            print("❌ upload to S3 fail")
            return

        video_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
        print(f"✅ upload to S3，video_url: {video_url}")

        # 4. call Apps Script
        remote_page = call_appscript(
            video_path=path,
            survey_data=survey_data,
            video_name=video_name,
            video_url=video_url
        )

        if remote_page:
            print(f"link: {remote_page}")
            
        # 5. notifier
            notify(video_name, remote_page)
            
        # 6. GUI callback
            try:
                self.callback(video_name, remote_page)
            except TypeError:
                self.callback(video_name)
        else:
            print("❌ Apps Script fail")
            try:
                self.callback(video_name)
            except TypeError:
                pass










