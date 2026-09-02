from typing import TYPE_CHECKING

from core.constants import (
    RENDER_HEIGHT_MAX_VALUE,
    RENDER_HEIGHT_MIN_VALUE,
    RENDER_SAMPLES_MAX_VALUE,
    RENDER_SAMPLES_MIN_VALUE,
    RENDER_WIDTH_MAX_VALUE,
    RENDER_WIDTH_MIN_VALUE,
)
from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.core import Base

if TYPE_CHECKING:
    from infrastructure.database.models import File, Project


class Render(Base):
    __tablename__ = "renders"

    width: Mapped[int]
    height: Mapped[int]
    samples: Mapped[int]
    denoiser: Mapped[bool]
    gpu: Mapped[bool]

    file_id: Mapped[int | None] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
    )
    file: Mapped["File"] = relationship(
        "File",
        foreign_keys=[file_id],
        back_populates="render",
    )
    project: Mapped["Project"] = relationship(
        "Project",
        foreign_keys="Project.render_id",
        back_populates="render",
    )

    __table_args__ = (
        CheckConstraint(
            f"""
            width >= {RENDER_WIDTH_MIN_VALUE}
            AND width <= {RENDER_WIDTH_MAX_VALUE}
            """,
            name="value_width",
        ),
        CheckConstraint(
            f"""
            height >= {RENDER_HEIGHT_MIN_VALUE}
            AND height <= {RENDER_HEIGHT_MAX_VALUE}
            """,
            name="value_height",
        ),
        CheckConstraint(
            f"""
            samples >= {RENDER_SAMPLES_MIN_VALUE}
            AND samples <= {RENDER_SAMPLES_MAX_VALUE}
            """,
            name="value_samples",
        ),
    )
