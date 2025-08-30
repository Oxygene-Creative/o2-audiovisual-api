from app.core.redis import redis_router as asr_broker
from faststream.redis import StreamSub

async def _process_batch(messages):
    print(f"Processing batch of {len(messages)} messages")
    for msg in messages:
        # Process each message
        print(f"Processing: {msg}")


@asr_broker.subscriber(stream=StreamSub(
        "audiovisual:asr_stream",
        group="av:asr_group",
        consumer="asr_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_asr_worker_1(messages):
    return


@asr_broker.subscriber(stream=StreamSub(
        "audiovisual:asr_stream",
        group="av:asr_group",
        consumer="asr_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_asr_worker_2(messages):
    return

@asr_broker.subscriber(stream=StreamSub(
        "audiovisual:asr_stream",
        group="av:asr_group",
        consumer="asr_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_asr_worker_3(messages):
    return