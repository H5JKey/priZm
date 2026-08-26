from fastapi import APIRouter

from .details_views import router as details_views_router
from .list_views import router as list_views_router

router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
)

router.include_router(list_views_router)
router.include_router(details_views_router)
