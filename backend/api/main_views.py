from fastapi import (
    APIRouter,
    Request,
    status,
)

router = APIRouter(
    tags=["Main"],
)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def read_root(
    request: Request,
    name: str = "Nikolay",
) -> dict[str, str]:
    docs_url = request.url.replace(
        path="/docs",
        query="",
    )
    return {
        "message": f"Hello {name}!",
        "docs_url": str(docs_url),
    }


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
)
async def check_health() -> dict[str, str]:
    return {"status": "ok"}
