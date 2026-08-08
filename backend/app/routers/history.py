from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/questions")
def get_recent_questions(
    user_name: str = "default_user",
    db: Session = Depends(get_db),
):
    questions = (
        db.query(models.Question, models.StudyMaterial)
        .join(
            models.StudyMaterial, 
            models.Question.material_id == models.StudyMaterial.id,
        )
        .filter(models.StudyMaterial.user_name == user_name)
        .order_by(models.Question.created_at.desc())
        .limit(20)
        .all()
    )
    
    return [
        {
            "id": question.id,
            "user_name": material.user_name,
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
    user_name: str = "default_user",
    db: Session = Depends(get_db)
):
    wrong_answers = (
        db.query(models.WrongAnswer)
        .filter(models.WrongAnswer.user_name == user_name)
        .order_by(models.WrongAnswer.created_at.desc())
        .limit(20)
        .all()
    )
    
    return [
        {
            "id": wrong_answer.id,
            "user_name": wrong_answer.user_name,
            "question_id": wrong_answer.question_id,
            "user_answer": wrong_answer.user_answer,
            "correct_answer": wrong_answer.correct_answer,
            "concept_tag": wrong_answer.concept_tag,
            "feedback": wrong_answer.feedback,
            "is_correct": wrong_answer.is_correct,
            "created_at": wrong_answer.created_at,
        }
        for wrong_answer in wrong_answers
    ]
