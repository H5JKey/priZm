from typing import TYPE_CHECKING

from core.constants import (
    FILE_BUCKET_MAX_LENGTH,
    FILE_KEY_MAX_LENGTH,
    FILE_NAME_MAX_LENGTH,
    FILE_NAME_MIN_LENGTH,
    FILE_SIZE_MAX_VALUE_BYTES,
    FILE_SIZE_MIN_VALUE_BYTES,
)
from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.core import Base

if TYPE_CHECKING:
    from infrastructure.database.models import Project, Render


class File(Base):
    __tablename__ = "files"

    name: Mapped[str] = mapped_column(String(FILE_NAME_MAX_LENGTH))
    size: Mapped[int]
    bucket: Mapped[str] = mapped_column(String(FILE_BUCKET_MAX_LENGTH))
    key: Mapped[str] = mapped_column(String(FILE_KEY_MAX_LENGTH))

    project_as_source_file: Mapped["Project"] = relationship(
        "Project",
        foreign_keys="Project.source_file_id",
        back_populates="source_file",
    )
    render: Mapped["Render"] = relationship(
        "Render",
        foreign_keys="Render.file_id",
        back_populates="file",
    )

    __table_args__ = (
        CheckConstraint(
            f"""
            LENGTH(name) >= {FILE_NAME_MIN_LENGTH}
            AND LENGTH(name) <= {FILE_NAME_MAX_LENGTH}
            """,
            name="length_file_name",
        ),
        CheckConstraint(
            f"""
            size > {FILE_SIZE_MIN_VALUE_BYTES}
            AND size <= {FILE_SIZE_MAX_VALUE_BYTES}
            """,
            name="value_size",
        ),
    )
