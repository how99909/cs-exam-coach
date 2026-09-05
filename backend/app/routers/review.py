from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dependencies import get_current_user
from app.services import review_service
from app.services.exceptions import InvalidRequestError

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/recommendations")
def get_review_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = review_service.get_weak_concepts(
        db=db,
        user_id=current_user.id,
    )

    return result


@router.get("/study-plan")
def get_study_plan(
    exam_date: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = review_service.get_study_plan(
            db=db,
            user_id=current_user.id,
            user_name=current_user.user_name,
            exam_date=exam_date,
        )
        
    except InvalidRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
        
    return result
