# AVAS

## Change in new version Jun3
- Packaged WebUI deployment into init_aw_webui.py
- Move all configuration to config.py(includes Google sheet,AWS configuration ...)
- Made sensitive information into environment variables, and use init_env.py to help users build .env
- Added automatic deletion of related videos after questionnaire submission (refers to deleting corresponding videos on S3)

## Change in new version May 25
- to avoid re-submission,every generated pages will be destroyed after sumbit result
- in everyday 1 am,delete all the generated pages existed over 7 days(even it was'not been submitted)

## Change in new version May 12
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

## Amazon S3 sign up and bucket creation
- Go to website https://aws.amazon.com/cn/s3/
- click sign up and finish the signing up

- S3 part
- sign in and search S3
- create a new bucket
- go to permission of the bucket
- to make sure appscript can get the link of the video
- finish the storing strategy of the bucket,a example can be:
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

- IAM part
- search IAM
- create a new user
- finish the strategy settings to make sure python can upload videos
- a example can be :
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


## Installation & Configuration
- The basic steps includes:
- 0.sign up in AWS and create bucket(see Amazon S3 sign up and bucket creation)
- 1.install requirements.txt
- 2.run init_aw_webui.py 
- 3.aws configure
- 4.run init_env.py 
- in this stage , I divide 1,2,3,4 to test its functionality.
- when everything can be finished well , they can be merged in one .py file 

```
git clone <repository_url>
cd <repository_folder>
aws configure
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 init_aw_webui.py #Do this step in terminal instead of IDE
python3 init_env.py #Do this step in terminal instead of IDE
```
- change/set other non-sensitive configuration in config.py

## Usage Instructions
```bash
python3 -m core.main
```
- then it will start monitor the target folder automatically
 
## ActivityWatch(This part in only for back-up operation when init_aw_webui.py fail)
- The default ActivityWatch web UI does **not** support parsing URLs to extract specific timestamps. It only supports:

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
```
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




