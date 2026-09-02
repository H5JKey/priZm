from pydantic import BaseModel

from schemas.constraints.user import (
    EmailConstraint,
    NameConstraint,
    PasswordConstraint,
    SurnameConstraint,
    UsernameConstraint,
)


class RegisterRequest(BaseModel):
    """
    Схема для регистрации пользователя.
    """

    surname: SurnameConstraint
    name: NameConstraint
    username: UsernameConstraint
    email: EmailConstraint
    password: PasswordConstraint


class LoginRequest(BaseModel):
    """
    Схема для входа пользователя в приложение.
    """

    username: UsernameConstraint
    password: PasswordConstraint
