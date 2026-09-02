from typing import Annotated

from fastapi import Depends, Query
from infrastructure.database.repositories.render import RenderRepository
from infrastructure.database.unit_of_work import UnitOfWork
from infrastructure.minio.client import MinioClient
from schemas.auth import LoginRequest
from services.auth import AuthService
from services.file_uploader import FileUploader
from services.project import ProjectService
from services.tag import TagService
from services.user import UserService

from dependencies.auth import (
    get_auth_user_by_access_token,
    get_auth_user_by_refresh_token,
    get_login_request,
)
from dependencies.minio import get_minio_client
from dependencies.repositories import get_render_repository, get_unit_of_work
from dependencies.services import (
    get_auth_service,
    get_input_file_uploader,
    get_project_service,
    get_tag_service,
    get_user_service,
)

InputFileUploaderDep = Annotated[
    FileUploader,
    Depends(get_input_file_uploader),
]

UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]

AuthServiceDep = Annotated[
    AuthService,
    Depends(get_auth_service),
]

TagServiceDep = Annotated[
    TagService,
    Depends(get_tag_service),
]

AuthUserByAccessTokenDep = Annotated[
    int,
    Depends(get_auth_user_by_access_token),
]

AuthUserByRefreshTokenDep = Annotated[
    int,
    Depends(get_auth_user_by_refresh_token),
]

LoginRequestDep = Annotated[
    LoginRequest,
    Depends(get_login_request),
]


ProjectServiceDep = Annotated[
    ProjectService,
    Depends(get_project_service),
]

RenderRepositoryDep = Annotated[
    RenderRepository,
    Depends(get_render_repository),
]

UnitOfWorkDep = Annotated[
    UnitOfWork,
    Depends(get_unit_of_work),
]

MinioClientDep = Annotated[
    MinioClient,
    Depends(get_minio_client),
]

PaginationSizeDep = Annotated[
    int,
    Query(
        ge=1,
    ),
]

PaginationPageDep = Annotated[
    int,
    Query(
        ge=1,
    ),
]
