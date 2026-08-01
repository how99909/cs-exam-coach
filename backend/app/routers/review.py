from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from app.database import get_db

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/recommendations")
def get_review_recommendations(
    user_name: str = "default_user",
    db: Session = Depends(get_db)
):
    results = (
        db.query(
            models.WrongAnswer.concept_tag,
            func.count(models.WrongAnswer.id).label("wrong_count")
        )
        .filter(models.WrongAnswer.user_name == user_name)
        .filter(models.WrongAnswer.is_correct == False)
        .group_by(models.WrongAnswer.concept_tag)
        .order_by(func.count(models.WrongAnswer.id).desc())
        .all()
    )
    
    return [
        {
            "user_name": user_name,
            "concept_tag": concept_tag or "미분류",
            "wrong_count": wrong_count,
            "recommendation": f"{concept_tag or '미분류'} 개념을 우선 복습하세요."
        }
        for concept_tag, wrong_count in results
    ]