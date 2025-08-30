from app.core.redis import redis_router as vad_broker
from faststream.redis import StreamSub


async def _process_vad(messages):
    print(f"Processing batch of {len(messages)} messages")
    for msg in messages:
        # Process each message
        print(f"Processing: {msg}")

@vad_broker.subscriber(stream=StreamSub(
        "audiovisual:vad_stream",
        group="audiovisual:vad_group",
        consumer="vad_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_vad_worker_1(messages):
    return


@vad_broker.subscriber(stream=StreamSub(
        "audiovisual:vad_stream",
        group="audiovisual:vad_group",
        consumer="vad_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_vad_worker_2(messages):
    return

@vad_broker.subscriber(stream=StreamSub(
        "audiovisual:vad_stream",
        group="audiovisual:vad_group",
        consumer="vad_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_vad_worker_3(messages):
    return