import os
import time
import json
import subprocess
import threading
import queue
import datetime
from watchdog.events import FileSystemEventHandler

from .s3_uploader import upload_to_s3
from .appscript_client import call_appscript_batch
from .notifier import notify_batch
from .config import SURVEY_JSON_PATH, S3_BUCKET_NAME, BATCH_INTERVAL

class VideoHandler(FileSystemEventHandler):
    def __init__(self, callback, wait_timeout=300, wait_interval=1, batch_interval=None):
        super().__init__()
        self.batch_interval = batch_interval if batch_interval is not None else BATCH_INTERVAL
        self.callback       = callback
        self.wait_timeout   = wait_timeout
        self.wait_interval  = wait_interval

        self._skip   = set()
        self._queue  = queue.Queue()
        self._timer  = None
        self._lock   = threading.Lock()

    def on_created(self, event):
        if event.is_directory:
            return
        path = event.src_path
        ext  = os.path.splitext(path)[1].lower()
        if ext not in ('.mov', '.avi', '.mp4'):
            return

        with self._lock:
            if path in self._skip:
                self._skip.remove(path)
                return
            
            
            self._queue.put(path)
            

            if self._timer is None:
                self._timer = threading.Timer(self.batch_interval, self._run_batch)
                self._timer.start()

    def _run_batch(self):
        with self._lock:
            self._timer = None  

        items = []
        while not self._queue.empty():
            items.append(self._queue.get())

        if not items:
            return

        # survey
        survey_data = {}
        if os.path.exists(SURVEY_JSON_PATH):
            try:
                with open(SURVEY_JSON_PATH, 'r', encoding='utf-8') as f:
                    survey_data = json.load(f)
            except:
                pass

        video_names = []
        video_urls  = []
        video_times = []

        for path in set(items):
            if not self._wait_for_stable_file(path):
                continue

            # get the time of the orginal video
            ts = os.path.getmtime(path)
            iso_ts = datetime.datetime.fromtimestamp(ts).isoformat()
            video_times.append(iso_ts)

            # convert to .mp4
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

            video_names.append(os.path.basename(path))
            video_urls.append(f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}")

        if not video_names:
            return

        page_url = call_appscript_batch(
            video_paths  = list(set(items)),
            video_names  = video_names,
            video_urls   = video_urls,
            video_times  = video_times,   
            survey_data  = survey_data
        ) or video_urls[0]

        notify_batch(video_names, [page_url])
        try:
            self.callback(video_names, [page_url])
        except TypeError:
            pass

    def _wait_for_stable_file(self, path):
        start = time.time()
        last_size    = -1
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
                last_size    = size
                stable_count = 0

            time.sleep(self.wait_interval)

        return False



















