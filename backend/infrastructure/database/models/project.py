from datetime import datetime
from typing import TYPE_CHECKING

from core.constants import (
    PROJECT_DESCRIPTION_MAX_LENGTH,
    PROJECT_NAME_MAX_LENGTH,
    PROJECT_NAME_MIN_LENGTH,
    ProjectVisibility,
    RenderStatus,
)
from sqlalchemy import CheckConstraint, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.core import Base

if TYPE_CHECKING:
    from infrastructure.database.models import File, Render, Tag, User


class Project(Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(PROJECT_NAME_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(
        String(PROJECT_DESCRIPTION_MAX_LENGTH),
    )
    create_date: Mapped[datetime] = mapped_column(
        server_default=func.timezone("UTC", func.now()),
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    source_file_id: Mapped[int] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
    )
    render_id: Mapped[int] = mapped_column(
        ForeignKey("renders.id", ondelete="CASCADE"),
    )
    status: Mapped[RenderStatus] = mapped_column(
        Enum(RenderStatus, name="render_status"),
        server_default=RenderStatus.rendering.value,
    )
    visibility: Mapped[ProjectVisibility] = mapped_column(
        Enum(ProjectVisibility, name="project_visibility"),
        server_default=ProjectVisibility.public.value,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
    )
    source_file: Mapped["File"] = relationship(
        "File",
        foreign_keys=[source_file_id],
        back_populates="project_as_source_file",
    )
    render: Mapped["Render"] = relationship(
        "Render",
        foreign_keys=[render_id],
        back_populates="project",
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        foreign_keys="Tag.project_id",
        back_populates="project",
    )

    __table_args__ = (
        CheckConstraint(
            f"""
            LENGTH(name) >= {PROJECT_NAME_MIN_LENGTH}
            AND LENGTH(name) <= {PROJECT_NAME_MAX_LENGTH}
            """,
            name="length_project_name",
        ),
    )
