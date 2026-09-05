from typing import Any

from sqlalchemy.orm import Session

from app import models
from app.ai import grading_ai
from app.services.exceptions import ResourceNotFoundError


def grade_answer(
    db: Session,
    *,
    user_id: int,
    question_id: int,
    user_answer: str,
) -> dict[str, Any]:
    question = (
        db.query(models.Question)
        .join(
            models.StudyMaterial,
            models.Question.material_id == models.StudyMaterial.id,
        )
        .filter(models.Question.id == question_id)
        .filter(
            models.StudyMaterial.user_id == user_id
        )
        .first()
    )
    
    if question is None:
        raise ResourceNotFoundError(
            "문제를 찾을 수 없습니다."
        )
    
    result = grading_ai.grade_answer(
        question_text=question.question_text,
        correct_answer=question.answer,
        user_answer=user_answer,
        concept=question.concept,
    )
    
    wrong_answer = models.WrongAnswer(
        user_id=user_id,
        question_id=question.id,
        user_answer=user_answer,
        correct_answer=question.answer,
        concept=result.get("concept") or question.concept,
        feedback=result.get("feedback", ""),
        is_correct=result.get("is_correct", False),
    )
    
    try:
        db.add(wrong_answer)
        db.commit()
        db.refresh(wrong_answer)
        
    except Exception:
        db.rollback()
        raise
    
    return result
