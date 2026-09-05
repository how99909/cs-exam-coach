from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services import grading_service
from app.services.exceptions import ResourceNotFoundError

router = APIRouter(prefix="/grading", tags=["grading"])


@router.post("/grade")
def grade_answer(
    request: schemas.GradeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return grading_service.grade_answer(
            db=db,
            user_id=current_user.id,
            question_id=request.question_id,
            user_answer=request.user_answer,
        )
        
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
