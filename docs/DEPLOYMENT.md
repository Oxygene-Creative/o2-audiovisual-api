# Deployment Guide

This service ingests TV/radio media and runs a staged analysis pipeline (segmentation -> audience -> ASR -> NLP -> LLM) backed by Redis Streams and Elasticsearch.

## Prerequisites

- Python `3.10`
- Redis (single node or cluster)
- Elasticsearch
- GraphQL API connectivity for dynamic config + metadata
- GCP credentials for media storage operations
- ffmpeg/poppler/OpenCV runtime dependencies

## Local Run (without Docker)

From `o2-audiovisual-api` root:

```bash
pipenv install
pipenv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker Run

From `o2-audiovisual-api` root:

```bash
docker build -t av-api .
docker run --rm \
  --name av-api \
  -p 8210:8210 \
  --env-file .env \
  av-api
```

The container starts with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8210 --root-path /api/av
```

## Build and Push (Artifact Registry)

```bash
gcloud builds submit --region=us-west2 --tag us-west2-docker.pkg.dev/oxygene-monitor/o2-monitor/av-api:latest
```

## Troubleshooting

In general, check open issues/PR discussions and then validate environment/runtime wiring.

### General errors

- Ensure Python and dependency versions are aligned with `Pipfile`.
- Validate Redis and Elasticsearch are reachable from the running process/container.
- Verify GraphQL endpoint and API key before startup, because config bootstrap depends on them.

### Startup and connectivity errors

- If app loops on startup with Redis errors, confirm `REDIS_URI`/`REDIS_BROKER_URI` and cluster seed format.
- If startup fails in `setup_env()`, validate `GRAPHQL_URI` and `GRAPHQL_API_KEY`.
- If media ingestion fails early, ensure ffmpeg is available in runtime.

### Ingestion and pipeline errors

- `POST /ingestion` 404 `blob_not_found`:
  - Source `bucket/blob` does not exist in GCS.
- Strict blob validation failures (`blob_validation_failed`):
  - Disable strict mode or fix GCS access/path.
- Stuck incomplete documents:
  - Trigger `POST /reingestion` and inspect stream-specific worker logs.

### AI stage integration errors

- Segmentation/ASR/NLP stage failures often indicate upstream AI service URL or timeout issues:
  - `SEGMENTATION_GPU_URL`
  - `AI_API_URL`
  - `SEGMENTATION_*_TIMEOUT_SECONDS`

### Practical checks

- Confirm API responds and routers are mounted.
- Validate one full ingestion request end-to-end.
- Verify ES documents advance through `status.step` until `complete=true`.
