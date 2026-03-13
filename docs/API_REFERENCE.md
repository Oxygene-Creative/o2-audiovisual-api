# API Reference

## Base URL

- Local dev (no root path): `http://localhost:8000`
- Docker runtime default includes root path `/api/av` on port `8210`

## Endpoints

### Ingestion

- `POST /ingestion`
  - Enqueues a new media item into priority queue for staged processing.
  - Body fields: `stream_id`, `stream_name`, `media_type`, `bucket`, `blob`, optional `timestamp_str`.

- `POST /reingestion`
  - Re-queues incomplete Elasticsearch documents based on `status.step`.

### Analysis

- `POST /analysis/ads-and-engagement`
  - Input: `{ "text": "..." }`
  - Runs LLM extraction for ads/show/engagement signals.

### Uploads

- `POST /uploads-from-pi`
  - Multipart upload endpoint for `.ts` files from edge/PI workflows.
  - Form fields: `file`, `stream_id`, `stream_name`, `timestamp`.
  - Converts to `.mp4`, uploads to GCS, returns upload metadata.

## Request Notes

- `/ingestion` expects JSON payload.
- `/uploads-from-pi` expects `multipart/form-data`.
- `/analysis/ads-and-engagement` expects JSON body.

## Pipeline Behavior

After `/ingestion`, work progresses through internal stream stages:

1. `INGESTION`
2. `AUDIENCE`
3. `ASR`
4. `NLP`
5. `LLM`

Final state sets `status.complete=true` in Elasticsearch.

## Related Docs

- Deep architecture and processing details: `docs/processing pipeline.md`
- Deployment: `docs/DEPLOYMENT.md`
- Environment variables: `docs/ENVIRONMENT.md`
