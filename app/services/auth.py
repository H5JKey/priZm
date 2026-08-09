from core.constants import BEARER_TOKEN_TYPE
from core.exceptions.auth import InvalidPasswordError
from core.exceptions.user import (
    UserEmailAlreadyExistsError,
    UserIdNotFoundError,
    UserUsernameAlreadyExistsError,
    UserUsernameNotFoundError,
)
from core.interfaces.clients import AbstractUnitOfWorkClient
from core.logging import get_logger
from core.security.jwt_tokens.factory import create_access_token, create_token
from core.security.password_utils import (
    convert_register_to_create_user,
    validate_password,
)
from infrastructure.database.repositories.user import UserRepository
from schemas.auth import LoginRequest, RegisterRequest
from schemas.token import TokenInfo
from schemas.user import UserResponse

logger = get_logger(__name__)


class AuthService:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWorkClient,
    ) -> None:
        self.unit_of_work = unit_of_work
        self.user_repository = self.unit_of_work.get_repository(UserRepository)

    async def register(self, register_user_data: RegisterRequest) -> TokenInfo:
        user = await self.user_repository.get_by_username(register_user_data.username)
        if user is not None:
            raise UserUsernameAlreadyExistsError(register_user_data.username)
        user = await self.user_repository.get_by_email(register_user_data.email)
        if user is not None:
            raise UserEmailAlreadyExistsError(register_user_data.email)

        create_user_data = convert_register_to_create_user(register_user_data)
        user = await self.user_repository.create_user(create_user_data)
        user_response = UserResponse.model_validate(user)
        token = create_token(user_response)
        logger.info(
            "User registered, user_id=%s, username=%s",
            user_response.id,
            register_user_data.username,
        )
        return token

    async def authenticate_user(
        self,
        auth_user_data: LoginRequest,
    ) -> TokenInfo:
        user = await self.user_repository.get_by_username(auth_user_data.username)
        if user is None:
            raise UserUsernameNotFoundError(auth_user_data.username)

        password = auth_user_data.password
        encrypted_password = user.encrypted_password
        if not validate_password(
            password=password,
            encrypted_password=encrypted_password,
        ):
            raise InvalidPasswordError(password)

        user_response = UserResponse.model_validate(user)
        token = create_token(user_response)
        logger.info(
            "User authed, user_id=%s, username=%s",
            user.id,
            auth_user_data.username,
        )
        return token

    async def refresh_access_token(self, user_id: int) -> TokenInfo:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserIdNotFoundError(user_id)

        user_response = UserResponse.model_validate(user)
        access_token = create_access_token(user_response)
        token = TokenInfo(
            access_token=access_token,
            token_type=BEARER_TOKEN_TYPE,
        )
        logger.info("User refreshed auth token, user_id=%s", user_id)
        return token
