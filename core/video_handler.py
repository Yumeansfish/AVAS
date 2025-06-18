import os
import threading
import queue
import datetime
from pathlib import Path
from watchdog.events import FileSystemEventHandler

from .video_metadata import (
    extract_timestamp_from_filename,
    get_fallback_timestamp,
    get_video_duration,
    calculate_end_time
)
from .survey_loader import load_survey_data
from .video_processor import convert_to_mp4, process_and_upload_video
from .appscript_client import call_appscript_batch
from .notifier import notify_batch
from .config import BATCH_INTERVAL


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
        """
        # reset timer and drain queue atomically
        with self._lock:
            self._timer = None
            items = []
            while not self._queue.empty():
                items.append(self._queue.get())

        if not items:
            return
        
        
        
        
        video_names = []
        video_urls = []
        video_times = []
        video_end_times = []
        survey_data_list = []

        for path in set(items):
            if not self._wait_for_stable_file(path):
                continue

            # Extract metadata
            filename = os.path.basename(path)
            iso_ts, video_time = extract_timestamp_from_filename(filename)
            
            print(f"\n=== Processing {filename} ===")
            print(f"Full path: {path}")
            print(f"Extracted from filename: iso_ts={iso_ts}, video_time={video_time}")
            
            if not iso_ts:
                iso_ts = get_fallback_timestamp(path)
                print(f"Using fallback timestamp: {iso_ts}")
                # Extract HH:MM from file modification time
                dt = datetime.datetime.fromisoformat(iso_ts)
                video_time = dt.strftime("%H:%M")
                print(f"Extracted video_time from fallback: {video_time}")
            print("=============================\n")

            video_times.append(iso_ts)

            # Get video duration and calculate end time
            duration = get_video_duration(path)
            print(f"Video duration: {duration} seconds")
            end_time = calculate_end_time(iso_ts, duration)
            print(f"Calculated end time: {end_time}")
            video_end_times.append(end_time)

            # Load survey data
            video_survey_data = load_survey_data()
            print(f"Loaded survey data: {video_survey_data}")
            survey_data_list.append(video_survey_data)

            # Convert and upload
            # pre-mark the target .mp4 to skip its creation event
            base, _ = os.path.splitext(path)
            expected_mp4 = base + ".mp4"
            with self._lock:
                self._skip.add(expected_mp4)

            mp4_path, should_skip = convert_to_mp4(path)
            if should_skip:
                with self._lock:
                    self._skip.add(mp4_path)

            video_url = process_and_upload_video(mp4_path)
            if not video_url:
                continue

            video_names.append(filename)
            video_urls.append(video_url)

        if not video_names:
            return

        print(f"\n=== Final batch data ===")
        print(f"Video names: {video_names}")
        print(f"Video times: {video_times}")
        print(f"Video end times: {video_end_times}")
        print(f"Survey files selected: {[s.get('_survey_file', 'unknown') for s in survey_data_list]}")
        print("========================\n")

        # Call Apps Script
        page_url = (
            call_appscript_batch(
                video_paths=list(set(items)),
                video_names=video_names,
                video_urls=video_urls,
                video_times=video_times,
                video_end_times=video_end_times,
                survey_data_list=survey_data_list,
            )
            or video_urls[0]
        )

        # Send notifications
        notify_batch(video_names, [page_url])
        try:
            self.callback(video_names, [page_url])
        except TypeError:
            pass
        
        # Clean up converted MP4 files after successful batch processing
        converted_files_to_delete = []
        for path in self._skip:
            if os.path.exists(path) and path.endswith('.mp4'):
                converted_files_to_delete.append(path)
                
        for file_path in converted_files_to_delete:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
        # Clear the skip set after cleanup
        self._skip.clear()

    def _wait_for_stable_file(self, path):
        """
        - get size of the file in every wait_interval seconds.
        - Considers the file stable after two identical size readings.
        - Aborts and returns False if wait_timeout is exceeded.
        """
        import time
        
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
