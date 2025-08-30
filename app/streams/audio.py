from app.core.redis import redis_router as audio_broker
from faststream.redis import StreamSub

async def _process_batch(messages):
    print(f"Processing batch of {len(messages)} messages")
    for msg in messages:
        # Process each message
        print(f"Processing: {msg}")


@audio_broker.subscriber(stream=StreamSub(
        "audiovisual:audio_stream",
        group="audiovisual:audio_group",
        consumer="audio_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audio_worker_1(messages):
    return


@audio_broker.subscriber(stream=StreamSub(
        "audiovisual:audio_stream",
        group="audiovisual:audio_group",
        consumer="audio_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audio_worker_2(messages):
    return

@audio_broker.subscriber(stream=StreamSub(
        "audiovisual:audio_stream",
        group="audiovisual:audio_group",
        consumer="audio_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audio_worker_3(messages):
    return