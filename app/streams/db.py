from app.core.redis import redis_router as db_broker
from faststream.redis import StreamSub

async def _process_batch(messages):
    print(f"Processing batch of {len(messages)} messages")
    for msg in messages:
        # Process each message
        print(f"Processing: {msg}")


@db_broker.subscriber(stream=StreamSub(
        "audiovisual:db_stream",
        group="av:db_group",
        consumer="db_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_db_worker_1(messages):
    return


@db_broker.subscriber(stream=StreamSub(
        "audiovisual:db_stream",
        group="av:db_group",
        consumer="db_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_db_worker_2(messages):
    return

@db_broker.subscriber(stream=StreamSub(
        "audiovisual:db_stream",
        group="av:db_group",
        consumer="db_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_db_worker_3(messages):
    return