from collections.abc import AsyncGenerator

from core.config.application import settings
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

metadata = MetaData(
    naming_convention=settings.database.naming_convention,
)


class Base(DeclarativeBase):
    """
    Базовый класс для наследования моделей базы данных.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    metadata: MetaData = metadata  # type: ignore[misc]


engine = create_async_engine(
    url=settings.database.url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    pool_recycle=settings.database.pool_recycle,
    echo=settings.database.echo,
)

session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=settings.database.expire_on_commit,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session
