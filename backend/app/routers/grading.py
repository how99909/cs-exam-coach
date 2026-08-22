from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, ai_service
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/grading", tags=["grading"])


@router.post("/grade")
def grade_answer(
    request: schemas.GradeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    question = (
        db.query(models.Question)
        .join(
            models.StudyMaterial,
            models.Question.material_id == models.StudyMaterial.id,
        )
        .filter(models.Question.id == request.question_id)
        .filter(
            models.StudyMaterial.user_id == current_user.id
        )
        .first()
    )
    
    if question is None:
        raise HTTPException(
            status_code=404,
            detail="문제를 찾을 수 없습니다.",
        )
    
    result = ai_service.grade_answer(
        question_text=question.question_text,
        correct_answer=question.answer,
        user_answer=request.user_answer,
        concept=question.concept,
    )
    
    wrong_answer = models.WrongAnswer(
        user_id=current_user.id,
        question_id=question.id,
        user_answer=request.user_answer,
        correct_answer=question.answer,
        concept=result.get("concept") or question.concept,
        feedback=result.get("feedback", ""),
        is_correct=result.get("is_correct", False),
    )
    
    db.add(wrong_answer)
    db.commit()
    db.refresh(wrong_answer)
    
    return result
