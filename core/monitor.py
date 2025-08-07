import os
import time
import threading
from watchdog.observers import Observer
from .video_handler import VideoHandler
from .offline_handler import OfflineHandler

class MonitorCore:
    def __init__(self):
        self.observer = None
        self.thread = None
        self.video_handler = None
        self.offline_handler = None
        self.state_update_thread = None
        self.running = False

    def start(self, watch_dir: str, callback):
        if not os.path.exists(watch_dir):
            raise FileNotFoundError(f"directory doesnot exsit: {watch_dir}")

        self.running = True
        
        handler = VideoHandler(callback)
        self.video_handler = handler
        
        self.offline_handler = OfflineHandler(watch_dir)
        offline_files = self.offline_handler.check_and_process_offline_files(handler)
        
        if offline_files:
            print(f"Processed {len(offline_files)} offline files")
        
        self.observer = Observer()
        self.observer.schedule(handler, watch_dir, recursive=False)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
        self.state_update_thread = threading.Thread(target=self._periodic_state_update, daemon=True)
        self.state_update_thread.start()
        
        print(f"start monitoring: {watch_dir}")

    def _periodic_state_update(self):
        while self.running:
            time.sleep(60)
            if self.offline_handler and self.running:
                self.offline_handler.update_state()

    def _run(self):
        self.observer.start()
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        self.observer.join()

    def stop(self):
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        if self.offline_handler:
            self.offline_handler.update_state()
        print("stop monitoring.")























