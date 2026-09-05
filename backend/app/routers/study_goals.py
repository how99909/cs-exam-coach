from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.services.study import goal_service

router = APIRouter(prefix="/study-goals", tags=["study-goals"])


@router.post("")
def create_study_goal(
    request: schemas.StudyGoalCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = goal_service.create_goal(
            db=db,
            user_id=current_user.id,
            subject=request.subject,
            title=request.title,
            target_score=request.target_score,
            exam_date=request.exam_date,
        )
    except InvalidRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    
    return {
        "success": True,
        "message": "학습 목표가 생성되었습니다",
        "goal": _serialize_goal(result),
    }
    
    
@router.get("")
def list_study_goals(
    subject: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = goal_service.list_goals(
        db=db,
        user_id=current_user.id,
        subject=subject,
    )
    
    return {
        "success": True,
        "goal_count": len(result),
        "goals": [_serialize_goal(goal, include_days_left=True) for goal in result],
    }
    
    
@router.get("/{goal_id}/status")
def get_study_goal_status(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = goal_service.get_goal_status(
            goal_id=goal_id,
            user_id=current_user.id,
            db=db,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
        
    return {
        "success": True,
        **result,
    }

    
@router.post("/strategy")
def generate_study_goal_strategy(
    request: schemas.StudyGoalStrategyRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = goal_service.generate_goal_strategy(
            db=db,
            user_id=current_user.id,
            user_name=current_user.user_name,
            goal_id=request.goal_id,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    
    return {
        "success": True,
        "message": "목표 달성 전략이 생성되었습니다.",
        **result,
    }


def _serialize_goal(
    goal: models.StudyGoal,
    *,
    include_days_left: bool = False,
) -> dict:
    result = {
        "id": goal.id,
        "subject": goal.subject,
        "title": goal.title,
        "target_score": goal.target_score,
        "exam_date": goal.exam_date,
        "created_at": goal.created_at,
    }

    if include_days_left:
        result["days_left"] = (goal.exam_date - date.today()).days

    return result
