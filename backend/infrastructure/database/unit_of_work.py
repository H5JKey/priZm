from types import TracebackType
from typing import Self

from core.interfaces.clients import AbstractUnitOfWorkClient
from core.interfaces.repositories import AbstractRepository
from core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class UnitOfWork(AbstractUnitOfWorkClient):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    def get_repository(
        self,
        repository_class: type[AbstractRepository],
    ) -> AbstractRepository:
        repository = repository_class(self.session)  # type: ignore[call-arg]
        return repository

    async def rollback(self) -> None:
        await self.session.rollback()
        logger.warning("Rolled back transaction, transaction_id=%s", id(self.session))

    async def commit(self) -> None:
        await self.session.commit()
        logger.debug("Commited transaction, transaction_id=%s", id(self.session))
