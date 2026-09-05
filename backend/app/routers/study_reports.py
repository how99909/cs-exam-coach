from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.analytics import report_service
from app.services.exceptions import ResourceNotFoundError

router = APIRouter(prefix="/study-reports", tags=["study-reports"])


@router.post("/generate")
def generate_personal_study_report(
    request: schemas.StudyReportRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = report_service.generate_personal_report(
            db=db,
            user_id=current_user.id,
            user_name=current_user.user_name,
            subject=request.subject,
            limit=request.limit,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "success": True,
        "message": "개인 맞춤 학습 리포트가 생성되었습니다.",
        **result,
    }
