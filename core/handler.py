import os
import time
import json
import subprocess
import threading
import queue
import datetime
import re
from pathlib import Path  
from watchdog.events import FileSystemEventHandler

from .s3_uploader import upload_to_s3
from .appscript_client import call_appscript_batch
from .notifier import notify_batch
from .config import (
    SURVEY_JSON_PATH,
    S3_BUCKET_NAME,
    BATCH_INTERVAL,
    PROJECT_ROOT,
)  


class VideoHandler(FileSystemEventHandler):
    """
    1. Waits for each file to finish writing.
    2. Converts non-.mp4 files to .mp4 via ffmpeg.
    3. Uploads the resulting files to S3.
    4. Calls an App Script to generate a page URL.
    5. Sends a notification and invokes a user callback.
    """

    def __init__(
        self, callback, wait_timeout=300, wait_interval=1, batch_interval=None
    ):
        super().__init__()
        self.batch_interval = (
            batch_interval if batch_interval is not None else BATCH_INTERVAL
        )
        self.callback = callback
        self.wait_timeout = wait_timeout
        self.wait_interval = wait_interval

        self._skip = set()
        self._queue = queue.Queue()
        self._timer = None
        self._lock = threading.Lock()

    def on_created(self, event):
        """
        Handler for "created" events.

        Behavior:
        1.Ignores non-video extensions
        2.Skips any path in self._skip (for example, a .mp4 just converted by the original video file)
        3.if no timer is active, starts a timer in batch_interval times.
        """
        if event.is_directory:
            return
        path = event.src_path
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".mov", ".avi", ".mp4"):
            return

        with self._lock:
            if path in self._skip:
                self._skip.remove(path)
                return

            self._queue.put(path)

            if self._timer is None:
                self._timer = threading.Timer(self.batch_interval, self._run_batch)
                self._timer.start()

    def _get_survey_for_time(self, video_time, survey_mapping):
        """
        return the selected survey based on the video time
        """
        time_points = survey_mapping.get('time_points', [])
        selected_survey = survey_mapping.get('default_survey', 'questions.json')

        for point in sorted(time_points, key=lambda x: x['time'], reverse=True):
            if point['time'] <= video_time:
                selected_survey = point.get('survey_file', 'questions.json')
                break
        return selected_survey
    
    def _run_batch(self):
        """
        batch all the videos in the queue after the timer finish

        Steps:
        1. Dequeues all file
        2. For each one:
           a. Waits for the file to stabilize (_wait_for_stable_file).
           b. Records its last-modified timestamp.
           c. Converts to .mp4 (marking the new .mp4 in self._skip).
           d. Uploads the .mp4 to S3 via upload_to_s3().
        3. Calls call_appscript_batch() with video metadata to get a page URL.
        4. Sends notifications (notify_batch) and invokes the callback.


        note:meaning of paramaters (for example,video_name...)are in docstring of function
        call_appscript_batch.
        """

        with self._lock:
            self._timer = None

        items = []
        while not self._queue.empty():
            items.append(self._queue.get())

        if not items:
            return

        # survey
        survey_mapping = {}
        mapping_path = Path(PROJECT_ROOT) / "data" / "surveys" / "survey_mapping.json"
        if os.path.exists(mapping_path):
            try:
                with open(mapping_path, "r", encoding="utf-8") as f:
                    survey_mapping = json.load(f)
            except:
                pass

        video_names = []
        video_urls = []
        video_times = []
        survey_data_list = [] 

        for path in set(items):
            if not self._wait_for_stable_file(path):
                continue

            # Extract timestamp from filename
            filename = os.path.basename(path)
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
                survey_file = self._get_survey_for_time(video_time, survey_mapping)
            else:
                # Fallback to file modification time if timestamp not found in filename
                ts = os.path.getmtime(path)
                iso_ts = datetime.datetime.fromtimestamp(ts).isoformat()
                survey_file = survey_mapping.get("default_survey", "questions.json")

            video_times.append(iso_ts)

            survey_path = Path(PROJECT_ROOT) / "data" / "surveys" / survey_file
            video_survey_data = {}
            if os.path.exists(survey_path):
                try:
                    with open(survey_path, "r", encoding="utf-8") as f:
                        video_survey_data = json.load(f)
                    video_survey_data["_survey_file"] = survey_file
                except:
                    pass
            else:
                if os.path.exists(SURVEY_JSON_PATH):
                    try:
                        with open(SURVEY_JSON_PATH, "r", encoding="utf-8") as f:
                            video_survey_data = json.load(f)
                    except:
                        pass

            survey_data_list.append(video_survey_data)

            # convert to .mp4
            ext = os.path.splitext(path)[1].lower()
            if ext != ".mp4":
                mp4_path = os.path.splitext(path)[0] + ".mp4"
                self._skip.add(mp4_path)
                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            path,
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

        page_url = (
            call_appscript_batch(
                video_paths=list(set(items)),
                video_names=video_names,
                video_urls=video_urls,
                video_times=video_times,
                survey_data_list=survey_data_list,
            )
            or video_urls[0]
        )

        notify_batch(video_names, [page_url])
        try:
            self.callback(video_names, [page_url])
        except TypeError:
            pass

    def _wait_for_stable_file(self, path):
        """
        - get size of the file in every wait_interval seconds.
        - Considers the file stable after two identical size readings.
        - Aborts and returns False if wait_timeout is exceeded.
        """
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
                last_size = size
                stable_count = 0

            time.sleep(self.wait_interval)

        return False
