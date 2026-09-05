from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services import exam_attempt_service
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError

router = APIRouter(prefix="/exam-attempts", tags=["exam-attempts"])


@router.post("/submit")
def submit_exam_attempt(
    request: schemas.ExamAttemptSubmitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
): 
    try:
        attempt, results = exam_attempt_service.submit_exam_attempt(
            db=db,
            user_id=current_user.id,
            subject=request.subject,
            title=request.title,
            answers=[
                (
                    item.question_id,
                    item.user_answer,
                )
                for item
                in request.answers
            ],
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
        "message": "시험 응시 결과가 저장되었습니다.",
        "attempt_id": attempt.id,
        "title": attempt.title,
        "subject": attempt.subject,
        "total_questions": attempt.total_questions,
        "correct_count": attempt.correct_count,
        "score": attempt.score,
        "results": results,
    }
    
    
@router.get("/history")
def get_exam_attempt_history(
    subject: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    attempts = exam_attempt_service.get_exam_attempt_history(
        db=db,
        user_id=current_user.id,
        subject=subject,
        limit=limit,
    )
    
    return {
        "success": True,
        "attempt_count": len(attempts),
        "attempts": [
            {
                "id": attempt.id,
                "subject": attempt.subject,
                "title": attempt.title,
                "total_questions": attempt.total_questions,
                "correct_count": attempt.correct_count,
                "score": attempt.score,
                "created_at": attempt.created_at,
            }
            for attempt in attempts
        ],
    }
    
    
@router.get("/{attempt_id:int}")
def get_exam_attempt_detail(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        attempt, answers = exam_attempt_service.get_exam_attempt_detail(
            db=db,
            user_id=current_user.id,
            attempt_id=attempt_id,
        )
        
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    
    return {
        "success": True,
        "attempt": {
            "id": attempt.id,
            "subject": attempt.subject,
            "title": attempt.title,
            "total_questions": attempt.total_questions,
            "correct_count": attempt.correct_count,
            "score": attempt.score,
            "created_at": attempt.created_at,
        },
        "answers": [
            {
                "question_id": question.id,
                "question": question.question_text,
                "user_answer": answer.user_answer,
                "correct_answer": question.answer,
                "is_correct": answer.is_correct,
                "feedback": answer.feedback,
                "concept": question.concept,
            }
            for answer, question in answers
        ],
    }
    
    
@router.get("/analytics")
def get_exam_attempt_analytics(
    subject: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    analytics = exam_attempt_service.get_exam_attempt_analytics(
        db=db,
        user_id=current_user.id,
        subject=subject,
        limit=limit,
    )
    
    if analytics["attempt_count"] == 0:
        return {
            "success": True,
            "message": (
                "응시 기록이 없습니다."
            ),
            **analytics,
        }
    
    return {
        "success": True,
        **analytics,
    }
