__all__ = ("router",)

from fastapi import APIRouter

from api.api_v1.projects import router as project_router
from api.api_v1.tags import router as tag_router

from .auth import router as auth_router
from .upload_file import router as upload_file_router
from .users import router as user_router

router = APIRouter(
    prefix="/v1",
)

router.include_router(auth_router)
router.include_router(upload_file_router)
router.include_router(project_router)
router.include_router(tag_router)
router.include_router(user_router)
