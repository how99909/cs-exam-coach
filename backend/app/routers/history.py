from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/questions")
def get_recent_questions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    questions = (
        db.query(models.Question, models.StudyMaterial)
        .join(
            models.StudyMaterial, 
            models.Question.material_id == models.StudyMaterial.id,
        )
        .filter(models.StudyMaterial.user_id == current_user.id)
        .order_by(models.Question.created_at.desc())
        .limit(20)
        .all()
    )
    
    return [
        {
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
        for question, material in questions
    ]
    
    
@router.get("/wrong-answers")
def get_recent_wrong_answers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    wrong_answers = (
        db.query(models.WrongAnswer)
        .filter(models.WrongAnswer.user_id == current_user.id)
        .order_by(models.WrongAnswer.created_at.desc())
        .limit(20)
        .all()
    )
    
    return [
        {
            "id": wrong_answer.id,
            "question_id": wrong_answer.question_id,
            "user_answer": wrong_answer.user_answer,
            "correct_answer": wrong_answer.correct_answer,
            "concept": wrong_answer.concept,
            "feedback": wrong_answer.feedback,
            "is_correct": wrong_answer.is_correct,
            "created_at": wrong_answer.created_at,
        }
        for wrong_answer in wrong_answers
    ]
