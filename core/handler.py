import os
import time
import json
import subprocess
import threading
import queue
from watchdog.events import FileSystemEventHandler
from .s3_uploader import upload_to_s3
from .appscript_client import call_appscript
from .notifier import notify_batch
from .config import SURVEY_JSON_PATH, S3_BUCKET_NAME

class VideoHandler(FileSystemEventHandler):
    def __init__(self, callback, wait_timeout=300, wait_interval=1, batch_interval=10):
        super().__init__()
        self.callback = callback
        self.wait_timeout = wait_timeout
        self.wait_interval = wait_interval
        self.batch_interval = batch_interval
        self._skip = set()
        self._queue = queue.Queue()
        self._timer = None
        self._lock = threading.Lock()

    def on_created(self, event):
        if event.is_directory:
            return
        path = event.src_path
        ext = os.path.splitext(path)[1].lower()
        if ext not in ('.mov', '.avi', '.mp4'):
            return
        with self._lock:
            if path in self._skip:
                self._skip.remove(path)
                return
            self._queue.put(path)
            if not self._timer:
                self._timer = threading.Timer(self.batch_interval, self._run_batch)
                self._timer.start()

    def _run_batch(self):
        with self._lock:
            self._timer = None
        items = []
        while not self._queue.empty():
            items.append(self._queue.get())
        video_names = []
        video_urls = []

        for path in set(items):
            if not self._wait_for_stable_file(path):
                continue

            survey_data = {}
            if os.path.exists(SURVEY_JSON_PATH):
                try:
                    with open(SURVEY_JSON_PATH, 'r', encoding='utf-8') as f:
                        survey_data = json.load(f)
                except:
                    pass

            ext = os.path.splitext(path)[1].lower()
            if ext != '.mp4':
                mp4_path = os.path.splitext(path)[0] + '.mp4'
                self._skip.add(mp4_path)
                try:
                    subprocess.run([
                        "ffmpeg", "-y", "-i", path,
                        "-c:v", "libx264", "-c:a", "aac",
                        "-movflags", "+faststart", mp4_path
                    ], check=True)
                    upload_path = mp4_path
                except subprocess.CalledProcessError:
                    upload_path = path
            else:
                upload_path = path

            s3_key = upload_to_s3(upload_path)
            if not s3_key:
                continue
            video_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
            video_name = os.path.basename(path)

            try:
                remote_page = call_appscript(
                    video_path=path,
                    survey_data=survey_data,
                    video_name=video_name,
                    video_url=video_url
                ) or video_url
            except:
                remote_page = video_url

            video_names.append(video_name)
            video_urls.append(remote_page)

        if video_names:
            notify_batch(video_names, video_urls)
            try:
                self.callback(video_names, video_urls)
            except TypeError:
                pass

    def _wait_for_stable_file(self, path):
        start = time.time()
        last_size = -1
        stable_count = 0
        while time.time() - start < self.wait_timeout:
            try:
                size = os.path.getsize(path)
            except OSError:
                return False
            if size == last_size:
                stable_count += 1
                if stable_count >= 2:
                    return True
            else:
                stable_count = 0
                last_size = size
            time.sleep(self.wait_interval)
        return False













