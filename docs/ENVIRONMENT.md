# Environment Variables

This document lists key environment variables for `o2-audiovisual-api`.

## Core Connectivity

- `REDIS_URI`: Redis endpoint(s). Supports single URI or comma-separated cluster seeds.
- `REDIS_BROKER_URI`: Optional explicit broker URI override.
- `GRAPHQL_URI`: GraphQL backend URL for config/tags/industries/stream updates.
- `GRAPHQL_API_KEY`: GraphQL API key used in `x-api-key` header.

## AI Service URLs

- `SEGMENTATION_GPU_URL`: Base URL for segmentation/VAD service.
- `AI_API_URL`: Base URL for ASR/NLP AI service.

## Ingestion Validation Controls

- `INGESTION_VALIDATE_GCS_BLOB`: `1` to validate source blob exists before enqueue.
- `INGESTION_VALIDATE_GCS_BLOB_STRICT`: `1` to fail request when validation check itself errors.

## Segmentation and Processing Tuning

- `SEGMENTATION_PREP_TIMEOUT_SECONDS`
- `SEGMENTATION_ITEM_TIMEOUT_SECONDS`
- `SEGMENTATION_REPLAY_LOG_PATH`
- `VIDEO_SLICE_TIMEOUT_SECONDS`
- `VIDEO_SLICE_CODEC`
- `AUDIO_EXTRACT_TIMEOUT_SECONDS`

## Runtime Flags

- `GRPC_FORK_SUPPORT_ENABLED`: Set by app startup (commonly `0`).

## Dynamic Config Values

At startup, `setup_env()` pulls config entries from GraphQL and injects them into process env.
Treat GraphQL config values as part of effective runtime configuration.

## Example `.env`

```env
REDIS_URI=redis://redis:6379
# Optional explicit broker URI
REDIS_BROKER_URI=redis://redis:6379

GRAPHQL_URI=https://example.com/graphql
GRAPHQL_API_KEY=

SEGMENTATION_GPU_URL=http://o2-ai:8000
AI_API_URL=http://o2-ai:8000

INGESTION_VALIDATE_GCS_BLOB=1
INGESTION_VALIDATE_GCS_BLOB_STRICT=0

SEGMENTATION_PREP_TIMEOUT_SECONDS=120
SEGMENTATION_ITEM_TIMEOUT_SECONDS=300
SEGMENTATION_REPLAY_LOG_PATH=/tmp/segmentation-replay.log
VIDEO_SLICE_TIMEOUT_SECONDS=120
VIDEO_SLICE_CODEC=libx264
AUDIO_EXTRACT_TIMEOUT_SECONDS=120
```

## Security Guidance

- Do not commit real API keys or secrets.
- Use secret management in deployment environments.
- Rotate compromised credentials immediately.
