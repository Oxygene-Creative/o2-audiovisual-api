# O2 Audiovisual API

Media ingestion and analysis pipeline API for o2 monitor workloads.
This service accepts TV/radio media inputs, orchestrates staged processing via Redis streams, and enriches content with segmentation, ASR, NLP, and LLM outputs before persisting analytics to Elasticsearch.

## Stack

- FastAPI + Uvicorn
- Redis (queueing and stream workers)
- Elasticsearch (analysis document storage)
- Google Cloud Storage (media assets)
- External AI services for segmentation, ASR, and NLP/LLM enrichment

## Quick Start

```bash
pipenv install
pipenv run uvicorn app.main:app --host=0.0.0.0 --port=8000 --reload
```

Service URL: `http://localhost:8000`

## Documentation

- Architecture and processing flow: `how-it-works.md`
- Deployment guide: `docs/DEPLOYMENT.md`
- Environment variables: `docs/ENVIRONMENT.md`
- API reference: `docs/API_REFERENCE.md`
- Pipeline deep-dive: `docs/processing pipeline.md`

## Run locally with docker
```bash
docker build -t av-api .
docker run --name av-api -p 8210:8210 -v ${PWD}:/code av-api
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
