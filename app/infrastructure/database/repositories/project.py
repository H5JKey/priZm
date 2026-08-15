from core.constants import ProjectVisibility, RenderStatus
from core.interfaces.repositories import AbstractProjectRepository
from core.logging import get_logger
from schemas.project import ProjectCreate, ProjectPartialUpdate
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from infrastructure.database.models import Project, Render, User

logger = get_logger(__name__)


class ProjectRepository(AbstractProjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, project_id: int) -> Project | None:
        stmt = (
            select(Project)
            .options(
                joinedload(Project.render).joinedload(Render.file),
                joinedload(Project.source_file),
            )
            .where(Project.id == project_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_project_owner(self, project_id: int) -> User | None:
        stmt = select(User).join(User.projects).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_user_projects(self, user_id: int) -> list[Project]:
        stmt = select(Project).where(Project.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_public_projects(
        self,
        user_id: int,
    ) -> list[Project]:
        stmt = select(Project).filter(
            and_(
                Project.user_id == user_id,
                Project.visibility == ProjectVisibility.public.value,
            ),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_project_status(self, project_id: int) -> Project | None:
        project = await self.get_by_id(project_id)
        if project is None:
            return None

        project.status = RenderStatus.completed.value  # type: ignore[assignment]
        await self.session.flush()
        logger.debug(
            "Updated project status in transaction, transaction_id=%s, project_id=%s, status=%s",  # noqa: E501
            id(self.session),
            project_id,
            project.status,
        )
        return project

    async def create_project(
        self,
        user_id: int,
        render_id: int,
        create_project_data: ProjectCreate,
    ) -> Project:
        project = Project(
            user_id=user_id,
            render_id=render_id,
            **create_project_data.model_dump(),
        )
        self.session.add(project)
        await self.session.flush()
        logger.debug(
            "Created project in transaction, transaction_id=%s, project_id=%s, name=%s, source_file_id=%s, visibility=%s",  # noqa: E501
            id(self.session),
            project.id,
            project.name,
            project.source_file_id,
            project.visibility,
        )
        return project

    async def partial_update_project(
        self,
        project_id: int,
        partial_update_project_data: ProjectPartialUpdate,
    ) -> Project | None:
        project = await self.get_by_id(project_id)
        if project is None:
            return None

        for field, value in partial_update_project_data.model_dump(
            exclude_none=True,
        ).items():
            setattr(project, field, value)

        await self.session.flush()
        logger.debug(
            "Updated project in transaction, transaction_id=%s, project_id=%s, name=%s, source_file_id=%s, visibility=%s",  # noqa: E501
            id(self.session),
            project.id,
            project.name,
            project.source_file_id,
            project.visibility,
        )
        return project

    async def delete_by_id(self, project_id: int) -> None:
        stmt = delete(Project).where(Project.id == project_id)
        await self.session.execute(stmt)
        await self.session.flush()
        logger.debug(
            "Deleted project in transaction, transaction_id=%s, project_id=%s",
            id(self.session),
            project_id,
        )
