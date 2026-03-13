# How `o2-audiovisual-api` Works

This repository implements an **audio/video analysis pipeline** for TV and radio content.
It combines:

- FastAPI HTTP endpoints for ingestion and utility operations
- Redis (streams + sorted set) for asynchronous processing
- Elasticsearch for storing/updating analysis documents
- Google Cloud Storage (GCS) for media assets
- External AI services for segmentation, ASR, NLP, and LLM enrichment
- Optional edge components (`media_server`, `pi_scripts`) for on-prem upload/forwarding

---

## 1) High-level architecture

There are three major execution contexts in this repo:

1. **Main AV API** (`app/`):
   - Receives ingestion requests
   - Pushes work into Redis
   - Runs multi-stage analysis workers
   - Persists results into Elasticsearch

2. **Media server** (`media_server/`):
   - Accepts large uploads from edge devices (e.g., TVHeadend/PI setup)
   - Converts/transcodes when needed
   - Uploads to GCS
   - Calls main AV API `/ingestion`

3. **PI scripts** (`pi_scripts/`):
   - Pull finished recordings from TVHeadend
   - Match channels to stream metadata via GraphQL
   - Upload recordings to media server endpoint

---

## 2) Main service boot and startup behavior

Entrypoint: `app/main.py`

- Creates FastAPI app and enables permissive CORS.
- Includes routers:
  - `/analysis/*` from `app/routers/ads.py`
  - `/uploads-from-pi` from `app/routers/pi_uploads.py`
  - `/ingestion` and `/reingestion` from `app/routers/ingestion.py`
- On startup:
  - Starts Redis broker (`redis_broker.start()`)
  - Loads dynamic env/config values from GraphQL (`setup_env()` in `app/core/config.py`)
  - Starts `queue_processor()` background task
- On shutdown:
  - Closes Redis broker

Important design detail: stream worker modules are imported in `main.py`, so their subscriber decorators register consumers at application import/start time.

---

## 3) Core data flow (end-to-end)

### Step A: Ingestion request

`POST /ingestion` accepts:
- `stream_id`, `stream_name`, `media_type` (`audio` or `video`), `bucket`, `blob`, optional `timestamp_str`

In `app/routers/ingestion.py` it:
- Builds a deterministic document id from blob path (`sha256(blob)`)
- Chooses ES index:
  - `radio_<stream_id>` for audio
  - `tv_<stream_id>` for video
- Creates initial metadata payload with status:
  - `status.complete = false`
  - `status.step = "INGESTION"`
- Pushes the payload into Redis sorted set:
  - key: `audiovisual:priority_queue`
  - score: timestamp epoch seconds

### Step B: Priority queue dispatcher

`app/streams/queue.py` continuously:
- Checks segmentation worker locks (simple backpressure gate)
- Pops next queued item via `ZPOPMAX` (newest score first)
- Publishes payload to `audiovisual:segmentation_stream`

### Step C: Segmentation stage

`app/streams/segmentation.py` workers:
- For video, ensures an `.mp3` blob exists (extracts from `.mp4` if needed)
- Calls external segmentation service: `POST {SEGMENTATION_GPU_URL}/vad/batch`
- Downloads master media from GCS
- Slices speech segments:
  - audio streams: slice `.mp3`
  - video streams: slice `.mp4` clips and also extract/upload segment soundtrack `.mp3`
- Uploads generated segments back to GCS
- Bulk-indexes segments in ES with status:
  - `status.step = "AUDIENCE"`
- Publishes segment document refs to `audiovisual:audience_stream`

### Step D: Audience stage

`app/streams/audience.py` workers:
- Fetch segment docs from ES (`mget`)
- Calls VAD endpoint again for male/female voice duration metrics
- Writes `audience` scores into `_updates`
- Updates ES status to `ASR`
- Publishes refs to `audiovisual:asr_stream`

### Step E: ASR stage

`app/streams/asr.py` workers:
- Fetch segment docs from ES
- Build ASR batch payload and call external AI `/asr/batch`
- Optionally post-process transcript text with LLM punctuation normalizer
- Stores:
  - `raw_text`
  - `language`
  - `language_score`
- Deletes temporary tv soundtrack blobs (`.mp3`) from GCS
- Updates ES status to `NLP`
- Publishes refs to `audiovisual:nlp_stream`

### Step F: NLP stage

`app/streams/nlp.py` workers:
- Fetch segment docs from ES
- Pull tags and industries from GraphQL
- Build batch requests for:
  - classification/tagging
  - topic extraction
  - emotion detection
  - sentiment analysis
  - text embeddings
- Writes NLP outputs into `_updates`
- Updates ES status to `LLM`
- Publishes refs to `audiovisual:llm_stream`

### Step G: LLM stage (final enrichment)

`app/streams/llm.py` workers:
- Fetch segment docs from ES
- Run `llm_transcript_analysis` to extract:
  - advertisements
  - show metadata (host/program)
  - audience engagement cues
- Maps convenience fields (`creator`, `title`)
- Updates `last seen` in GraphQL for TV/radio stream
- Updates ES final status:
  - `status.complete = true`
  - `status.step = null`

---

## 4) Reingestion and recovery

`POST /reingestion` in `app/routers/ingestion.py`:
- Searches ES for docs where `status.complete == false`
- Re-publishes each doc id to the correct Redis stream based on `status.step`
  - `INGESTION` -> segmentation stream
  - `AUDIENCE` -> audience stream
  - `ASR` -> asr stream
  - `NLP` -> nlp stream
  - `LLM` -> llm stream

Utility script: `scripts/claim_stuck_stream.py`
- Claims stale pending Redis stream messages for a consumer group (`XCLAIM`), useful for crashed consumers.

---

## 5) Supporting modules

### Storage and media

- `app/core/gcp.py`: GCS upload/download/delete/blob existence
- `app/core/media_processing.py`:
  - extract audio from video
  - slice audio/video segments
  - media integrity + size checks
- `app/core/files.py`: file path/size/folder helpers

### Persistence and messaging

- `app/core/es.py`:
  - sync ES client
  - bulk index/update helper
  - `mget` fetch for stream-stage docs
- `app/core/redis.py`:
  - supports both single Redis and Redis Cluster based on `REDIS_URI`
  - defines broker + shared redis client + worker locks

### External metadata/config

- `app/core/graphql.py`:
  - fetches runtime configs and tags/industries
  - updates stream `last seen`
  - wraps GraphQL requests with API key auth

### LLM and prompting

- `app/core/llm.py`:
  - primary model: Gemini (`gemini-2.5-flash-lite`)
  - fallback model: Azure OpenAI (`gpt-4o` deployment)
- `app/core/prompts.py`: transcript and ad/show/engagement prompts
- `app/analyzers/*`: thin async wrappers around external AI endpoints and local prompt chains

---

## 6) API surface (main AV app)

- `POST /ingestion` -> enqueue new media item
- `POST /reingestion` -> replay incomplete docs based on status
- `POST /analysis/ads-and-engagement` -> ad/show/engagement extraction from raw text
- `POST /uploads-from-pi` -> direct upload endpoint that validates `.ts`, converts to `.mp4`, uploads to GCS

---

## 7) Media server flow (optional but important)

`media_server/` is a companion service for handling large edge uploads.

Typical path:
1. PI/edge uploads file to media server `/uploads-from-pi`
2. Media server enqueues into `media_srv:priority_queue`
3. Media processing worker converts/validates media, uploads to GCS
4. Media server calls main AV API `/ingestion`
5. Main AV API pipeline continues through segmentation -> audience -> asr -> nlp -> llm

This decouples heavy upload/transcode from analysis workers.

---

## 8) Runtime dependencies and infra expectations

Key services expected at runtime:

- Redis (single node or cluster)
- Elasticsearch
- GraphQL API (for config/tag/industry metadata + updates)
- Google Cloud Storage credentials and target bucket
- AI services:
  - VAD/segmentation endpoint (`SEGMENTATION_GPU_URL`)
  - ASR + NLP endpoint (`AI_API_URL`)
  - LLM provider credentials (Gemini and/or Azure OpenAI fallback)

---

## 9) Build/test state in this repository

- Containerized runtime defined in `Dockerfile` (Python 3.10 + ffmpeg + OpenCV + uvicorn).
- Tests exist under `tests/`, but some reference older module paths (`app.pipelines.*`), indicating parts of the suite may be legacy relative to the current `app/streams/*` architecture.

---

## 10) Practical mental model

Think of this system as:

1. **Ingestion API** writes a unit of work
2. **Redis streams** move that work through deterministic stages
3. **Each stage enriches the same ES document** and advances `status.step`
4. **Failures are recoverable** via `reingestion` + stale message claiming
5. **Final artifacts** are segmented media in GCS + enriched structured metadata in ES/GraphQL

That is the operational core of `o2-audiovisual-api`.