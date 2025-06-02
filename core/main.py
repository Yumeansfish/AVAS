import signal
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

from core.config import WATCH_DIR
from core.monitor import MonitorCore

def main():
    core = MonitorCore()
    core.start(str(WATCH_DIR), callback=None) 
    def handle(sig, frame):
        print("stop monitoring")
        core.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, handle)
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()

