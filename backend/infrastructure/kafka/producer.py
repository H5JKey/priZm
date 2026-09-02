from aiokafka import AIOKafkaProducer, ConsumerRecord
from core.config.application import settings
from core.logging import get_logger
from schemas.event import AddRenderProjectEvent
from services.project import ProjectService

from infrastructure.database.core import session_factory
from infrastructure.database.unit_of_work import UnitOfWork
from infrastructure.minio.client import MinioClient
from infrastructure.minio.session import get_minio_session

logger = get_logger(__name__)

_producer = None


async def get_producer() -> AIOKafkaProducer:
    global _producer  # noqa: PLW0603
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka.bootstrap_servers,
        )
    return _producer


async def process_message(message: ConsumerRecord) -> None:
    json_data = message.value
    add_render_project_event = AddRenderProjectEvent.model_validate(
        json_data,
    )
    logger.info("Received message, %s", add_render_project_event)
    project_id = add_render_project_event.project_id
    minio_session = get_minio_session()
    async with (
        session_factory() as session,
        UnitOfWork(session) as unit_of_work,
        ProjectService(unit_of_work) as project_service,
        minio_session.create_client(
            "s3",
            **settings.minio.config,
        ) as client,
        MinioClient(client) as s3_client,
    ):
        await project_service.update_project_status(project_id)
        await project_service.add_render_to_project(
            add_render_project_event,
            s3_client,
        )
