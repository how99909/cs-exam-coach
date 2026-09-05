from sqlalchemy.orm import Session

from app import models


def get_recent_questions(
    db: Session,
    *,
    user_id: int,
    limit: int = 20,
) -> list[tuple[models.Question, models.StudyMaterial]]:
    return (
        db.query(models.Question, models.StudyMaterial)
        .join(
            models.StudyMaterial, 
            models.Question.material_id == models.StudyMaterial.id,
        )
        .filter(models.StudyMaterial.user_id == user_id)
        .order_by(models.Question.created_at.desc())
        .limit(limit)
        .all()
    )
    

def get_recent_wrong_answers(
    db: Session,
    *,
    user_id: int,
    limit: int = 20,
) -> list[models.WrongAnswer]:
    return (
        db.query(models.WrongAnswer)
        .filter(models.WrongAnswer.user_id == user_id)
        .order_by(models.WrongAnswer.created_at.desc())
        .limit(limit)
        .all()
    )
