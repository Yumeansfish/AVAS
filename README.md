# AVAS

## Main Change in new version
- delete gui folder and all the gui.py
- move the batch_interval setting from handler.py to config.py
- now every setting is finished in config.py
- merge all the videos files in the same webpage and only call appscript once
- add logic in appscript to handle the localhost url in the webpage

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
 
## ActivityWatch
-The default ActivityWatch web UI does **not** support parsing URLs to extract specific timestamps. It only supports:

- Showing the most recent timespan of activity  
- Jumping to a specific day  

- Therefore, I forked the [aw-webui](https://github.com/Yumeansfish/aw-webui) repository 
- and added front-end logic to parse `start` and `end` parameters from the URL, 
- allowing the UI to jump -to an exact time range. 
- This makes it possible to link videos on the final webpage to their corresponding timeline URLs.

- To implement it,please:

```
git clone https://github.com/Yumeansfish/aw-webui.git
```
- update Node to make sure that npm run build can executed successfully
- a example installing way :
```
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
source ~/.bashrc   
nvm install 23.11.0
nvm use 23.11.0
```
- then:
```
aw-webui % npm install
aw-webui % npm run build
- then apply the new dist to the activitywatch:
```
cp -r /home/trustme/aw-webui/dist/. /home/trustme/activitywatch/aw-server/aw_server/static/
//check whether it's the right path in computer
pkill -f activitywatch 
/home/trustme/activitywatch/aw-server/aw-server &   //restart
```
- after this, use this link to test whether its work :
- http://localhost:5600/#/timeline?start=2025-05-11T15%3A10%3A00&end=2025-05-11T15%3A30%3A00
- the left side of the timeline will start from 05-11 15:10
- the right side of the timeline will end at 05-11 15:30

 
## App script
- This project use App script to generate the pages including videos and surveys
- and collect the result of surveys to Google sheet
- to clear the properties to avoid achieve 500KB limit of app script
- run this code in app script code.gs
```
function clearAllPages() {
  PropertiesService.getScriptProperties().deleteAllProperties();
}
```

## Amazon S3 
- Go to website https://aws.amazon.com/cn/s3/
- click sign up and finish the signing up
- sign in and search S3
- create a new bucket
- go to permission of the bucket
- finish the storing strategy of the bucket
```
  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::avas/*"
        }
    ]
}
```
- then need to add the permission to python uploading
- search IAM
- create a new user
- finish the strategy settings
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"     
      ],
      "Resource": "arn:aws:s3:::avas/*"
    }
  ]
}
```
- dowload the .csv which contains the access key and secret key
- in AVAS,call terminal end enter:
```
aws configure
```
- then finish the configuration steps:
- configuration steps:
- `AWS_ACCESS_KEY_ID`  (in file)
- `AWS_SECRET_ACCESS_KEY`  (in file)
- eu-north-1
- json

## Google access key
- coming soon





## Installation & Configuration
```
git clone <repository_url>
cd <repository_folder>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
- set all the configuration in config.py



## Usage Instructions
-launch the GUI
```bash
python3 -m core.main
```
- then it will start monitor the target folder automatically



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




