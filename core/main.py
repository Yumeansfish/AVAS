import argparse
from .monitor import MonitorCore


def gui_callback(video_name: str, page_url: str = None):
    msg = f"Processing complete: {video_name}"
    if page_url:
        msg += f" -> {page_url}"
    print(msg)


def main():
    parser = argparse.ArgumentParser(description="AVAS video monitoring entry script")
    parser.add_argument(
        "--dir", required=True,
        help="Path to the directory to monitor for video files"
    )
    args = parser.parse_args()

    core = MonitorCore()
    core.start(args.dir, gui_callback)
    print("Monitoring in progress. Press Ctrl+C to stop.")


if __name__ == "__main__":
    main()
