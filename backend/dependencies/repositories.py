from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from infrastructure.database.core import get_session
from infrastructure.database.repositories.file import FileRepository
from infrastructure.database.repositories.project import ProjectRepository
from infrastructure.database.repositories.render import RenderRepository
from infrastructure.database.repositories.user import UserRepository
from infrastructure.database.unit_of_work import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession


async def get_file_repository(
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
) -> AsyncGenerator[FileRepository]:
    file_repository = FileRepository(session)
    yield file_repository


async def get_user_repository(
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
) -> AsyncGenerator[UserRepository]:
    user_repository = UserRepository(session)
    yield user_repository


async def get_project_repository(
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
) -> AsyncGenerator[ProjectRepository]:
    project_repository = ProjectRepository(session)
    yield project_repository


async def get_render_repository(
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
) -> AsyncGenerator[RenderRepository]:
    render_repository = RenderRepository(session)
    yield render_repository


async def get_unit_of_work(
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
) -> AsyncGenerator[UnitOfWork]:
    async with UnitOfWork(session) as unit_of_work:
        yield unit_of_work
