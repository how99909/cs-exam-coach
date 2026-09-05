from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dependencies import get_current_user
from app.services import material_service
from app.services.exceptions import InvalidRequestError

router = APIRouter(prefix="/materials", tags=["materials"])

@router.post("/extract-pdf")
def extract_pdf_text(
    subject: str = Form(...),
    start_page: int | None = Form(None, ge=1),
    end_page: int | None = Form(None, ge=1),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = material_service.extract_pdf(
            db=db,
            user_id=current_user.id,
            subject=subject,
            file_obj=file.file,
            filename=file.filename,
            start_page=start_page,
            end_page=end_page,
        )
        
    except InvalidRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
        
    return {
        "success": True,
        "user_name": current_user.user_name,
        **result,
    }
