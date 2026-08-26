__all__ = ("router",)
from fastapi import APIRouter

from .details_views import router as details_router
from .list_views import router as list_router

router = APIRouter(
    prefix="/projects",
    tags=["Project"],
)

router.include_router(list_router)
router.include_router(details_router)
