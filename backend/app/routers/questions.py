from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.services import question_service
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/questions", tags=["questions"])

@router.post("/generate")
def generate_questions(
    request: schemas.QuestionGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    material, questions = (
        question_service.generate_questions(
            db=db,
            user_id=current_user.id,
            subject=request.subject,
            content=request.content,
            question_type=request.question_type,
            count=request.count,
            difficulty=request.difficulty,
        )
    )

    return {
        "user_name": current_user.user_name,
        "material_id": material.id,
        "questions": [
            {
                "question_id": question.id,
                "question_text": question.question_text,
                "answer": question.answer,
                "explanation": question.explanation,
                "concept": question.concept,
                "question_type": question.question_type,
                "difficulty": question.difficulty,
            }
            for question in questions
        ],
    }
