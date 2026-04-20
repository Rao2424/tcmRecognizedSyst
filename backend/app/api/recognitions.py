from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .deps import get_db
from ..core.responses import success_response
from ..services.recognition_service import (
    RecognitionServiceError,
    recognize_herb_image,
)


router = APIRouter(prefix="/api/recognitions", tags=["recognitions"])


def _pick_first_non_empty(*values: str | None) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()

    return ""


@router.post("/herb-image")
async def recognize_single_herb_image(
    file: UploadFile = File(...),
    source_type: str = Form(default="album", alias="sourceType"),
    client_filename: str = Form(default="", alias="clientFilename"),
    client_content_type: str = Form(default="", alias="clientContentType"),
    db: Session = Depends(get_db),
):
    normalized_source_type = (source_type or "album").strip().lower()
    if normalized_source_type not in {"camera", "album"}:
        raise HTTPException(status_code=400, detail="sourceType 仅支持 camera 或 album")

    filename = _pick_first_non_empty(client_filename, file.filename)
    content_type = _pick_first_non_empty(client_content_type, file.content_type)

    try:
        image_bytes = await file.read()
        result = await recognize_herb_image(
            db=db,
            image_bytes=image_bytes,
            filename=filename,
            content_type=content_type,
        )
    except RecognitionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    finally:
        await file.close()

    return success_response(result)
