from app.core.redis import redis_router as nlp_broker
from faststream.redis import StreamSub

async def _process_batch(messages):
    print(f"Processing batch of {len(messages)} messages")
    for msg in messages:
        # Process each message
        print(f"Processing: {msg}")


@nlp_broker.subscriber(stream=StreamSub(
        "audiovisual:nlp_stream",
        group="audiovisual:nlp_group",
        consumer="nlp_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_nlp_worker_1(messages):
    return


@nlp_broker.subscriber(stream=StreamSub(
        "audiovisual:nlp_stream",
        group="audiovisual:nlp_group",
        consumer="nlp_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_nlp_worker_2(messages):
    return

@nlp_broker.subscriber(stream=StreamSub(
        "audiovisual:nlp_stream",
        group="audiovisual:nlp_group",
        consumer="nlp_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_nlp_worker_3(messages):
    return