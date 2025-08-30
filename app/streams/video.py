from app.core.redis import redis_router as video_broker
from faststream.redis import StreamSub

async def _process_batch(messages):
    print(f"Processing batch of {len(messages)} messages")
    for msg in messages:
        # Process each message
        print(f"Processing: {msg}")


@video_broker.subscriber(stream=StreamSub(
        "audiovisual:video_stream",
        group="audiovisual:video_group",
        consumer="video_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_video_worker_1(messages):
    return


@video_broker.subscriber(stream=StreamSub(
        "audiovisual:video_stream",
        group="audiovisual:video_group",
        consumer="video_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_video_worker_2(messages):
    return

@video_broker.subscriber(stream=StreamSub(
        "audiovisual:video_stream",
        group="audiovisual:video_group",
        consumer="video_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_video_worker_3(messages):
    return