from aiokafka import AIOKafkaConsumer
from core.config.application import settings

from infrastructure.kafka.producer import process_message
from infrastructure.kafka.utils import deserialize_message

_consumer = None


async def get_consumer() -> AIOKafkaConsumer:
    global _consumer
    if _consumer is None:
        _consumer = AIOKafkaConsumer(
            settings.kafka.topic.generate_render,
            bootstrap_servers=settings.kafka.bootstrap_servers,
            group_id="app",
            value_deserializer=deserialize_message,
        )
    return _consumer


async def consume(consumer: AIOKafkaConsumer) -> None:
    await consumer.start()
    async for message in consumer:
        await process_message(message)
        await consumer.commit()
