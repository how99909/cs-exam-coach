from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.analytics import report_service
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError

router = APIRouter(prefix="/weekly-reports", tags=["weekly-reports"])


@router.post("/generate")
def generate_weekly_report(
    request: schemas.WeeklyStudyReportRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = report_service.generate_weekly_report(
            db=db,
            user_id=current_user.id,
            user_name=current_user.user_name,
            subject=request.subject,
            days=request.days,
        )
    except InvalidRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    
    return {
        "success": True,
        "message": "주간 학습 리포트가 생성되었습니다",
        **result,
    }
