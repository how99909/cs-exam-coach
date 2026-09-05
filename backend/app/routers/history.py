from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dependencies import get_current_user
from app.services import history_service

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/questions")
def get_recent_questions(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    rows = history_service.get_recent_questions(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )

    return [
        _serialize_question(question, material)
        for question, material in rows
    ]
    
@router.get("/wrong-answers")
def get_recent_wrong_answers(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    items = history_service.get_recent_wrong_answers(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )

    return [_serialize_wrong_answer(item) for item in items]


def _serialize_question(
    question: models.Question,
    material: models.StudyMaterial,
) -> dict:
    return {
        "id": question.id,
        "material_id": question.material_id,
        "subject": material.subject,
        "question_text": question.question_text,
        "answer": question.answer,
        "explanation": question.explanation,
        "concept": question.concept,
        "question_type": question.question_type,
        "difficulty": question.difficulty,
        "created_at": question.created_at,
    }


def _serialize_wrong_answer(item: models.WrongAnswer) -> dict:
    return {
        "id": item.id,
        "question_id": item.question_id,
        "user_answer": item.user_answer,
        "correct_answer": item.correct_answer,
        "concept": item.concept,
        "feedback": item.feedback,
        "is_correct": item.is_correct,
        "created_at": item.created_at,
    }
