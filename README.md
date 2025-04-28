# AVAS

## Project Overview
The Video Handler module listens for new video files (`.mov`, `.avi`, `.mp4`) in a specified directory. Once a file has finished writing, non-MP4 videos are automatically transcoded to MP4 (H.264 + AAC, faststart). The resulting file is uploaded to AWS S3, a Google Apps Script endpoint is called to update or create a remote page, and a notification is sent. A GUI callback can be used to refresh the front end in real time.

## Key Features
- Automatic detection of new `.mov`, `.avi`, and `.mp4` files  
- Transcoding to MP4 with H.264 video, AAC audio, and `+faststart` for streaming  
- Skip handling of already–transcoded MP4 files to prevent duplication  
- Upload to a configurable S3 bucket  
- Integration with Google Apps Script for remote page updates  
- Notification support (e.g., email, Slack)  
- GUI callback interface for live front-end updates  

## Environment & Dependencies
- **Python:** 3.7 or higher  
- **System:** `ffmpeg` installed and available on `PATH`  
- **Python packages:**  
    - `watchdog`  
    - `boto3`  
    - `requests`  
    - Standard library: `json`, `subprocess`, etc.  

## Installation & Configuration
```bash
git clone <repository_url>
cd <repository_folder>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

1. Create or edit `core/config.py` (or set environment variables):  
   - `SURVEY_JSON_PATH`: Local path to the survey JSON file  
   - `S3_BUCKET_NAME`: Target AWS S3 bucket name  
2. Ensure AWS credentials are configured via environment variables or `~/.aws/credentials`:  
   - `AWS_ACCESS_KEY_ID`  
   - `AWS_SECRET_ACCESS_KEY`  
3. Configure Google Apps Script settings (script ID, API key, etc.) in `core/config.py` or via environment variables.

## Usage Instructions
Just launch the GUI and it will start watching for new videos automatically:  
```bash
python3 -m gui.monitor_gui
```

## Directory Structure
```text
<repository_root>/
    core/
        __init__.py
        appscript_client.py
        config.py
        handler.py
        main.py
        monitor.py
        notifier.py
        s3_uploader.py
    data/
        …
    gui/
        __init__.py
        monitor_gui.py
        survey_gui.py
    .gitignore
    client_secret.json
    credentials.json
    token.json
    README.md
```


