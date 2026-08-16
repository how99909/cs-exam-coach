from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas, ai_service
from app.database import get_db

router = APIRouter(prefix="/grading", tags=["grading"])


@router.post("/grade")
def grade_answer(
    request: schemas.GradeRequest,
    db: Session = Depends(get_db),
):
    result = ai_service.grade_answer(
        question_text=request.question_text,
        correct_answer=request.correct_answer,
        user_answer=request.user_answer,
        concept=request.concept,
    )
    
    wrong_answer = models.WrongAnswer(
        user_name=request.user_name,
        question_id=request.question_id,
        user_answer=request.user_answer,
        correct_answer=request.correct_answer,
        concept=result.get("concept") or request.concept,
        feedback=result.get("feedback", ""),
        is_correct=result.get("is_correct", False),
    )
    
    db.add(wrong_answer)
    db.commit()
    db.refresh(wrong_answer)
    
    return result
