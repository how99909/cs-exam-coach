from sqlalchemy.orm import Session

from app import models
from app.ai import question_ai


def generate_questions(
    db: Session,
    *,
    user_id: int,
    subject: str,
    content: str,
    question_type: str,
    count: int,
    difficulty: str,
) -> tuple[
    models.StudyMaterial,
    list[models.Question],
]:
    generated_questions = question_ai.generate_questions(
        subject=subject,
        content=content,
        question_type=question_type,
        count=count,
        difficulty=difficulty,
    )
    
    try:
        material = models.StudyMaterial(
            user_id=user_id,
            subject=subject,
            content=content,
        )
        db.add(material)
        db.flush()

        questions = []
        
        for item in generated_questions:
            question = models.Question(
                material_id=material.id,
                question_text=item.get("question_text", ""),
                answer=item.get("answer", ""),
                explanation=item.get("explanation", ""),
                concept=item.get("concept", item.get("concept_tag", "")),
                question_type=item.get("question_type", question_type),
                difficulty=difficulty,
            )
            
            db.add(question)
            questions.append(question)

        db.commit()
        
        db.refresh(material)
        
        for question in questions:
            db.refresh(question)
            
    except Exception:
        db.rollback()
        raise

    return material, questions