import os
import time
import json
import subprocess
from watchdog.events import FileSystemEventHandler
from .s3_uploader import upload_to_s3
from .appscript_client import call_appscript
from .notifier import notify
from .config import SURVEY_JSON_PATH, S3_BUCKET_NAME

class VideoHandler(FileSystemEventHandler):
    def __init__(self, callback, wait_timeout=300, wait_interval=1):
        super().__init__()
        self.callback = callback
        self._skip = set()
        self.wait_timeout = wait_timeout
        self.wait_interval = wait_interval

    def on_created(self, event):
        if event.is_directory:
            return

        src_path = event.src_path
        if src_path in self._skip:
            self._skip.remove(src_path)
            return

        ext = os.path.splitext(src_path)[1].lower()
        if ext not in ('.mov', '.avi', '.mp4'):
            return

        # wait until file is done writing
        if not self._wait_for_stable_file(src_path):
            print(f"⚠️ File not ready: {src_path}")
            return

        video_name = os.path.basename(src_path)
        print(f"New video detected: {video_name}")

        # load survey JSON if present
        survey_data = {}
        if os.path.exists(SURVEY_JSON_PATH):
            try:
                with open(SURVEY_JSON_PATH, 'r', encoding='utf-8') as f:
                    survey_data = json.load(f)
            except Exception as e:
                print(f"Failed to load survey: {e}")
        else:
            print("Survey JSON not found")

        # convert to .mp4 if needed
        if ext != '.mp4':
            base = os.path.splitext(src_path)[0]
            mp4_path = f"{base}.mp4"
            self._skip.add(mp4_path)
            try:
                print(f"Converting to MP4: {mp4_path}")
                subprocess.run([
                    "ffmpeg", "-y", "-i", src_path,
                    "-c:v", "libx264", "-c:a", "aac",
                    "-movflags", "+faststart",
                    mp4_path
                ], check=True)
                print(f"✅ Conversion complete: {mp4_path}")
                upload_path = mp4_path
            except subprocess.CalledProcessError as e:
                print(f"❌ Conversion failed: {e}")
                upload_path = src_path
        else:
            upload_path = src_path

        # upload to S3
        s3_key = upload_to_s3(upload_path)
        if not s3_key:
            print("❌ S3 upload failed")
            return

        video_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
        print(f"✅ Uploaded to S3: {video_url}")

        # call Apps Script
        try:
            remote_page = call_appscript(
                video_path=src_path,
                survey_data=survey_data,
                video_name=video_name,
                video_url=video_url
            )
            if not remote_page:
                raise ValueError("Empty response from Apps Script")
            print(f"Remote page URL: {remote_page}")
        except Exception as e:
            print(f"❌ Apps Script call failed: {e}")
            remote_page = None

        # send notification
        if remote_page:
            notify(video_name, remote_page)

        # invoke GUI callback
        try:
            if remote_page:
                self.callback(video_name, remote_page)
            else:
                self.callback(video_name)
        except TypeError:
            self.callback(video_name)

    def _wait_for_stable_file(self, path):
        """
        Wait until the file size has not changed for two consecutive intervals,
        up to wait_timeout seconds.
        """
        start = time.time()
        last_size = -1
        stable_count = 0

        while time.time() - start < self.wait_timeout:
            try:
                current_size = os.path.getsize(path)
            except OSError:
                return False

            if current_size == last_size:
                stable_count += 1
                if stable_count >= 2:
                    return True
            else:
                stable_count = 0
                last_size = current_size

            time.sleep(self.wait_interval)

        return False











