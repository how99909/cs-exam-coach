from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas


def create_rag_feedback(
    db: Session,
    user_name: str,
    user_id: int,
    request: schemas.RagAnswerFeedbackCreate,
) -> models.RagAnswerFeedback:
    feedback = models.RagAnswerFeedback(
        user_id=user_id,
        subject=request.subject,
        material_id=request.material_id,
        question=request.question,
        answer=request.answer,
        accuracy_score=request.accuracy_score,
        grounding_score=request.grounding_score,
        source_relevance_score=request.source_relevance_score,
        helpfulness_score=request.helpfulness_score,
        comment=request.comment,
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return feedback


def get_rag_feedback_summary(
    db: Session,
    user_id: int | None = None,
    subject: str | None = None,
):
    query = db.query(
        func.count(models.RagAnswerFeedback.id).label("feedback_count"),            
        func.avg(models.RagAnswerFeedback.accuracy_score).label("avg_accuracy_score"),
        func.avg(models.RagAnswerFeedback.grounding_score).label("avg_grounding_score"),
        func.avg(models.RagAnswerFeedback.source_relevance_score).label(
            "avg_source_relevance_score"
        ),
        func.avg(models.RagAnswerFeedback.helpfulness_score).label(
            "avg_helpfulness_score"
        ),
    )
    
    if user_id:
        query = query.filter(models.RagAnswerFeedback.user_id == user_id)
        
    if subject:
        query = query.filter(models.RagAnswerFeedback.subject == subject)
    
    return query.first()


def get_recent_rag_feedback(
    db: Session,
    user_id: int | None = None,
    subject: str | None = None,
    limit: int = 20,
):
    query = db.query(models.RagAnswerFeedback)
        
    if user_id:
        query = query.filter(models.RagAnswerFeedback.user_id == user_id)
        
    if subject:
        query = query.filter(models.RagAnswerFeedback.subject == subject)
        
    return (
        query.order_by(models.RagAnswerFeedback.created_at.desc())
        .limit(limit)
        .all()
    )
