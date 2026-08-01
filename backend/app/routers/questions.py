from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas, ai_service
from app.database import get_db

router = APIRouter(prefix="/questions", tags=["questions"])

@router.post("/generate")
def generate_questions(
    request: schemas.QuestionGenerateRequest,
    db: Session = Depends(get_db),
):
    material = models.StudyMaterial(
        user_name=request.user_name,
        subject=request.subject,
        content=request.content,
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    generated_questions = ai_service.generate_questions(
        subject=request.subject,
        content=request.content,
        question_type=request.question_type,
        count=request.count,
        difficulty=request.difficulty,
    )
    
    saved_questions = []
    
    for item in generated_questions:
        question = models.Question(
            material_id=material.id,
            question_text=item.get("question_text", ""),
            answer=item.get("answer", ""),
            explanation=item.get("explanation", ""),
            concept_tag=item.get("concept_tag", ""),
            question_type=item.get("question_type", request.question_type),
        )
        
        db.add(question)
        db.commit()
        db.refresh(question)
        
        saved_questions.append(
            {
                "question_id": question.id,
                "question_text": question.question_text,
                "answer": question.answer,
                "explanation": question.explanation,
                "concept_tag": question.concept_tag,
                "question_type": question.question_type,
            }
        )
        
    return {
        "user_name": request.user_name,
        "material_id": material.id,
        "questions": saved_questions,
    }
