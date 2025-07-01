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

