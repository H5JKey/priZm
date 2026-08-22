from dependencies.annotations import InputFileUploaderDep
from dependencies.auth import get_auth_user_by_access_token
from fastapi import APIRouter, Depends, UploadFile, status
from schemas.file import FileResponse

router = APIRouter(
    tags=["Upload File"],
    prefix="/files",
    dependencies=[Depends(get_auth_user_by_access_token)],
)


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=FileResponse,
)
async def upload_file(
    uploaded_file: UploadFile,
    file_uploader: InputFileUploaderDep,
) -> FileResponse:
    return await file_uploader.upload(
        file_name=uploaded_file.filename,  # type: ignore[arg-type]
        file=uploaded_file.file,
    )
