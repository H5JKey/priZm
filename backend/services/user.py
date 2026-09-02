from typing import cast

from core.exceptions.user import UserIdNotFoundError
from core.interfaces.clients import AbstractUnitOfWorkClient
from core.logging import get_logger
from infrastructure.database.models import User
from infrastructure.database.repositories.user import UserRepository
from schemas.user import UserFullResponse, UserResponse, UserUpdate

logger = get_logger(__name__)


class UserService:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWorkClient,
    ) -> None:
        self.unit_of_work = unit_of_work
        self.user_repository = self.unit_of_work.get_repository(UserRepository)

    async def get_by_id(self, user_id: int) -> UserResponse:
        user_full_response = await self.get_profile_by_id(user_id)
        return UserResponse.model_validate(user_full_response)

    async def get_profile_by_id(self, user_id: int) -> UserFullResponse:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserIdNotFoundError(user_id)

        logger.info(
            "Received user, user_id=%s, username=%s",
            user_id,
            user.username,
        )
        return UserFullResponse.model_validate(user)

    async def update_user(
        self,
        user_id: int,
        update_user_data: UserUpdate,
    ) -> UserResponse:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserIdNotFoundError(user_id)

        user = await self.user_repository.update_user(
            user_id=user_id,
            update_user_data=update_user_data,
        )
        user = cast(User, user)
        logger.info(
            "Updated user, user_id=%s, username=%s",
            user_id,
            user.username,
        )
        return UserResponse.model_validate(user)

    async def delete_by_id(self, user_id: int) -> None:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserIdNotFoundError(user_id)

        logger.info(
            "Deleted user, user_id=%s, username=%s",
            user_id,
            user.username,
        )
        await self.user_repository.delete_by_id(user_id)
