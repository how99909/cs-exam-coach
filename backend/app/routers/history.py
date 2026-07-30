from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/questions")
def get_recent_questions(db: Session = Depends(get_db)):
    questions = (
        db.query(models.Question)
        .order_by(models.Question.created_at.desc())
        .limit(20)
        .all()
    )
    
    return [
        {
            "id": question.id,
            "material_id": question.material_id,
            "question_text": question.question_text,
            "answer": question.answer,
            "explanation": question.explanation,
            "concept_tag": question.concept_tag,
            "question_type": question.question_type,
            "created_at": question.created_at,
        }
        for question in questions
    ]
    
    
@router.get("/wrong-answers")
def get_recent_wrong_answers(db: Session = Depends(get_db)):
    wrong_answers = (
        db.query(models.WrongAnswer)
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
            "concept_tag": wrong_answer.concept_tag,
            "feedback": wrong_answer.feedback,
            "is_correct": wrong_answer.is_correct,
            "created_at": wrong_answer.created_at,
        }
        for wrong_answer in wrong_answers
    ]