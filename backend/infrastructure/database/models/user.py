from datetime import datetime
from typing import TYPE_CHECKING

from core.constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_EMAIL_MIN_LENGTH,
    USER_ENCRYPTED_PASSWORD_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_NAME_MIN_LENGTH,
    USER_SURNAME_MAX_LENGTH,
    USER_SURNAME_MIN_LENGTH,
    USER_USERNAME_MAX_LENGTH,
    USER_USERNAME_MIN_LENGTH,
)
from sqlalchemy import CheckConstraint, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.core import Base

if TYPE_CHECKING:
    from infrastructure.database.models import Project


class User(Base):
    __tablename__ = "users"

    surname: Mapped[str] = mapped_column(String(USER_SURNAME_MAX_LENGTH))
    name: Mapped[str] = mapped_column(String(USER_NAME_MAX_LENGTH))
    username: Mapped[str] = mapped_column(String(USER_USERNAME_MAX_LENGTH), unique=True)
    email: Mapped[str] = mapped_column(String(USER_EMAIL_MAX_LENGTH), unique=True)
    encrypted_password: Mapped[str] = mapped_column(
        String(USER_ENCRYPTED_PASSWORD_MAX_LENGTH),
    )
    registration_date: Mapped[datetime] = mapped_column(
        server_default=func.timezone("UTC", func.now()),
    )

    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="user",
    )

    __table_args__ = (
        CheckConstraint(
            f"""
            LENGTH(surname) >= {USER_SURNAME_MIN_LENGTH}
            AND LENGTH(surname) <= {USER_SURNAME_MAX_LENGTH}
            """,
            name="length_surname",
        ),
        CheckConstraint(
            f"""
            LENGTH(name) >= {USER_NAME_MIN_LENGTH}
            AND LENGTH(name) <= {USER_NAME_MAX_LENGTH}
            """,
            name="length_name",
        ),
        CheckConstraint(
            f"""
            LENGTH(username) >= {USER_USERNAME_MIN_LENGTH}
            AND LENGTH(username) <= {USER_USERNAME_MAX_LENGTH}
            """,
            name="length_username",
        ),
        CheckConstraint(
            f"""
            LENGTH(email) >= {USER_EMAIL_MIN_LENGTH}
            AND LENGTH(email) <= {USER_EMAIL_MAX_LENGTH}
            """,
            name="length_email",
        ),
    )
