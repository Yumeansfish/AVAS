# AVAS

## Project Overview
The Video Handler module listens for new video files (`.mov`, `.avi`, `.mp4`) in a specified directory. Once a file has finished writing, non-MP4 videos are automatically transcoded to MP4 (H.264 + AAC, faststart). The resulting file is uploaded to AWS S3, a Google Apps Script endpoint is called to update or create a remote page, and a notification is sent. 

## Key Features
- Automatic detection of new `.mov`, `.avi`, and `.mp4` files  
- Transcoding to MP4 with H.264 video, AAC audio, and `+faststart` for streaming  
- Skip handling of already–transcoded MP4 files to prevent duplication  
- Upload to a configurable S3 bucket  
- Integration with Google Apps Script for remote page updates  
- Notification by email
- Implement a queue in handler so that the videos entering in the folder in a given interval will be handled together

## Environment & Dependencies
- **Python:** 3.8  
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

1. install GUI dependencies
```
sudo apt update
sudo apt install -y python3-tk
```
2. Configure AWS
```
aws configure
```
- configuration steps:
- `AWS_ACCESS_KEY_ID`  (in file)
- `AWS_SECRET_ACCESS_KEY`  (in file)
- eu-north-1
- json
3. set the batch_interval in the following code in handler.py
```
def __init__(self, callback, wait_timeout=300, wait_interval=1, batch_interval=10):
```



## Usage Instructions
-launch the GUI
```bash
python3 -m gui.monitor_gui
```
- finish the survey configuration in the GUI 
- choose the target directory in the GUI
- click start monitoring


## Directory Structure
```text
<repository_root>/
├── core/
│   ├── __init__.py
│   ├── appscript_client.py
│   ├── config.py
│   ├── handler.py
│   ├── main.py
│   ├── monitor.py
│   ├── notifier.py
│   └── s3_uploader.py
├── data/
│   └── … 
├── gui/
│   ├── __init__.py
│   ├── monitor_gui.py
│   └── survey_gui.py
├── .gitignore
├── client_secret.json
├── credentials.json
├── token.json
└── README.md

```


