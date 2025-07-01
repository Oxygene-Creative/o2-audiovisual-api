# Audio-Visual API
API for that has data streams for processing audio, video and image data from various sources

## Install Dependencies
```bash
pipenv install
```

## Run locally
```bash
pipenv run uvicorn app.main:app --host=0.0.0.0 --port=8000 --reload
```

## Run locally with docker
```bash
docker build -t av-api .
docker run --name av-api -p 8210:8210 -v ${PWD}:/code av_api
```

## Build container and publish to gcloud artifact
```bash
gcloud builds submit --region=us-west2 --tag us-west2-docker.pkg.dev/oxygene-monitor/o2-monitor/av-api:latest
```

## Fix TvHeadend timers/autorec issue
Install tampermonkey browser extension and add the `pi scripts/timer_fix.js` script

## Setup TvHeadend System.d service

### Create upload tv service

```bash
sudo nano /etc/systemd/system/upload_tv.service
```

copy these file contents

```ini
[Unit]
Description=Upload TV Script
After=network.target

[Service]
ExecStart=/home/oxygene/o2/o2-audiovisual-api/pi_scripts/venv/bin/python upload_tv.py
WorkingDirectory=/home/oxygene/o2/o2-audiovisual-api/pi_scripts/
StandardOutput=append:/var/log/upload_tv.log
StandardError=append:/var/log/upload_tv_error.log
Restart=always
User=oxygene

[Install]
WantedBy=multi-user.target
```

### Create upload tv service timer
```bash
sudo nano /etc/systemd/system/upload_tv.timer
```

copy these file contents

```ini
[Unit]
Description=Timer for Upload TV Script

[Timer]
OnBootSec=10min
OnUnitActiveSec=4h
Unit=upload_tv.service

[Install]
WantedBy=timers.target
```

### Start the service
```bash
sudo systemctl daemon-reload
sudo systemctl start upload_tv.service
sudo systemctl enable upload_tv.service
sudo systemctl status upload_tv.service
```

### Check the logs
```bash
journalctl -u upload_tv.service
journalctl -u upload_tv.timer
```
