from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from schemas.constraints.user import (
    EmailConstraint,
    EncryptedPasswordConstraint,
    NameConstraint,
    SurnameConstraint,
    UsernameConstraint,
)


class UserBase(BaseModel):
    """
    Базовая схема для пользователя.
    """

    surname: SurnameConstraint
    name: NameConstraint
    username: UsernameConstraint

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """
    Схема для создания пользователя.
    """

    email: EmailConstraint
    encrypted_password: EncryptedPasswordConstraint


class UserUpdate(UserBase):
    """
    Схема для обновления данных о пользователе.
    """
    email: EmailConstraint

class UserResponse(UserBase):
    """
    Схема для вывода информации о пользователе,
    которая будет видна другим пользователям.
    """

    id: int
    registration_date: datetime


class UserFullResponse(UserResponse):
    """
    Схема для вывода информации о пользователе.
    """

    email: EmailConstraint
