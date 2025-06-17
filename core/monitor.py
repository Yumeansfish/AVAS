import os
import time
import threading
from watchdog.observers import Observer
from .video_handler import VideoHandler

class MonitorCore:
    def __init__(self):
        self.observer = None
        self.thread = None

    def start(self, watch_dir: str, callback):
        if not os.path.exists(watch_dir):
            raise FileNotFoundError(f"directory doesnot exsit: {watch_dir}")

        handler = VideoHandler(callback)
        self.observer = Observer()
        self.observer.schedule(handler, watch_dir, recursive=False)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"start monitoring: {watch_dir}")

    def _run(self):
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        self.observer.join()

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("stop monitoring。")























