from app.core.redis import redis_router as llm_broker
from faststream.redis import StreamSub

async def _process_batch(messages):
    print(f"Processing batch of {len(messages)} messages")
    for msg in messages:
        # Process each message
        print(f"Processing: {msg}")


@llm_broker.subscriber(stream=StreamSub(
        "audiovisual:llm_stream",
        group="av:llm_group",
        consumer="llm_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_llm_worker_1(messages):
    return


@llm_broker.subscriber(stream=StreamSub(
        "audiovisual:llm_stream",
        group="av:llm_group",
        consumer="llm_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_llm_worker_2(messages):
    return

@llm_broker.subscriber(stream=StreamSub(
        "audiovisual:llm_stream",
        group="av:llm_group",
        consumer="llm_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_llm_worker_3(messages):
    return