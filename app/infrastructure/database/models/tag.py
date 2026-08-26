from typing import TYPE_CHECKING

from core.constants import TAG_MAX_LENGTH, TAG_MIN_LENGTH
from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.core import Base
from infrastructure.database.models import Project

if TYPE_CHECKING:
    from infrastructure.database.models import Project


class Tag(Base):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(TAG_MAX_LENGTH))
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))

    project: Mapped["Project"] = relationship(
        "Project",
        foreign_keys=[project_id],
        back_populates="tags",
    )

    __table_args__ = (
        CheckConstraint(
            f"""
            LENGTH(name) >= {TAG_MIN_LENGTH}
            AND LENGTH(name) <= {TAG_MAX_LENGTH}
            """,
            name="length_tag_name",
        ),
    )
