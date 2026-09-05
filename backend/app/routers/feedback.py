from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.feedback import question_feedback_service
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/question")
def create_question_feedback(
    request: schemas.QuestionFeedbackCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = question_feedback_service.create_feedback(
            db=db,
            user_id=current_user.id,
            question_id=request.question_id,
            quality_score=request.quality_score,
            explanation_score=request.explanation_score,
            exam_relevance_score=request.exam_relevance_score,
            difficulty_match_score=request.difficulty_match_score,
            comment=request.comment,
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
        "message": "문제 평가가 저장되었습니다.",
        **result,
    }
    
    
@router.get("/question/{question_id}")
def get_question_feedback_summary(
    question_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = question_feedback_service.get_question_summary(
        db=db,
        user_id=current_user.id,
        question_id=question_id,
    )
        
    return result
    
    
@router.get("/summary")
def get_feedback_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = question_feedback_service.get_summary(
        db=db,
        user_id=current_user.id,
    )
        
    return result
    
    
@router.get("/low-score-questions")
def get_low_score_questions(
    threshold: float = Query(default=3.0, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = question_feedback_service.get_low_score_questions(
        db=db,
        user_id=current_user.id,
        threshold=threshold,
    )
    
    return result
    
    
@router.get("/low-exam-relevance")
def get_low_exam_relevance_questions(
    threshold: float = Query(default=3.0, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = question_feedback_service.get_low_exam_relevance_questions(
        db=db,
        user_id=current_user.id,
        threshold=threshold,
    )
    
    return result
    
    
@router.get("/recent-comments")
def get_recent_feedback_comments(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = question_feedback_service.get_recent_comments(
        db=db,
        user_id=current_user.id,
        user_name=current_user.user_name,
        limit=limit,
    )
    
    return result
    
    
@router.get("/admin-dashboard")
def get_admin_feedback_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = question_feedback_service.get_admin_dashboard(
        db=db,
        user_id=current_user.id,
        user_name=current_user.user_name,
    )
    
    return result
