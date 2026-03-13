# Processing Pipeline

## TV Processing

### 1) Upload service → media server
- The upload service sends the recording to the media server’s upload endpoint.
- The media server enqueues the job into `media_srv:priority_queue` and forwards it to `media_srv:media_processing`.
- Source:
  - media server upload handler: [media_server/routers/uploads.py](../media_server/routers/uploads.py)
  - media server queue worker: [media_server/streams/queue.py](../media_server/streams/queue.py)

### 2) Media processing → GCS + ingestion
- The media processor converts `.ts` to `.mp4` if needed, uploads the recording to GCS, then calls the AV API `/ingestion` endpoint.
- Source:
  - media processing worker: [media_server/streams/media_processing.py](../media_server/streams/media_processing.py)

### 3) AV ingestion → priority queue
- The AV API `/ingestion` stores metadata and pushes the job into `audiovisual:priority_queue`.
- Source:
  - ingestion API: [app/routers/ingestion.py](../app/routers/ingestion.py)

### 4) AV queue → segmentation stream
- The queue worker pops from `audiovisual:priority_queue` and publishes to `audiovisual:segmentation_stream`.
- Source:
  - queue worker: [app/streams/queue.py](../app/streams/queue.py)

### 5) Segmentation → AI VAD
- The segmentation worker prepares audio for VAD and calls the AI `/vad/batch` endpoint.
- For TV, if the `.mp3` audio blob does not exist, the worker downloads the `.mp4` master from GCS, extracts audio for the **whole file**, uploads the `.mp3`, then calls `/vad/batch` using that audio.
- VAD returns speech timestamps, which are used to slice the original `.mp4` into speech segments. Segments are uploaded and indexed to ES with `status.step = "AUDIENCE"`, then IDs are published to `audiovisual:audience_stream`.
- Source:
  - segmentation worker: [app/streams/segmentation.py](../app/streams/segmentation.py)
  - VAD endpoint: [../o2-ai/inference/routers/vad.py](../../o2-ai/inference/routers/vad.py)

### 6) Audience → ASR → NLP → LLM
- `audiovisual:audience_stream` → audience processing
- `audiovisual:asr_stream` → transcription
- `audiovisual:nlp_stream` → NLP
- `audiovisual:llm_stream` → LLM summaries/insights
- Source:
  - [app/streams/audience.py](../app/streams/audience.py)
  - [app/streams/asr.py](../app/streams/asr.py)
  - [app/streams/nlp.py](../app/streams/nlp.py)
  - [app/streams/llm.py](../app/streams/llm.py)


#### In summary
- audiovisual:priority_queue (ZSET): ingestion backlog ordered by timestamp.
- audiovisual:segmentation_stream: speech/music segmentation stage.
- audiovisual:audience_stream: audience (male/female) analysis stage.
- audiovisual:asr_stream: transcription (ASR) stage.
- audiovisual:nlp_stream: NLP/tagging stage.
- audiovisual:llm_stream: LLM/enrichment stage.