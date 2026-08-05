from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/rag-feedback", tags=["rag-feedback"])


def validate_score(score: int, field_name: str):
    if score < 1 or score > 5:
        return {
            "success": False,
            "message": f"{field_name}는 1점 이상 5점 이하이어야 합니다.",
        }
    return None


@router.post("/answer")
def create_rag_answer_feedback(
    request: schemas.RagAnswerFeedbackCreate, 
    db: Session = Depends(get_db)
):
    validations = [
        validate_score(request.accuracy_score, "accuracy_score"),
        validate_score(request.grounding_score, "grounding_score"),
        validate_score(request.source_relevance_score, "source_relevance_score"),
        validate_score(request.helpfulness_score, "helpfulness_score"),
    ]
    
    for validation in validations:
        if validation is not None:
            return validation
        
    feedback = models.RagAnswerFeedback(
        user_name = request.user_name,
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
    
    return {
        "success": True,
        "message": "RAG 답변 평가가 저장되었습니다.",
        "feedback_id": feedback.id,
    }
    
    
@router.get("/summary")
def get_rag_feedback_summary(
    user_name: str | None = None,
    subject: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        func.count(models.RagAnswerFeedback.id).label("feedback_count"),            
        func.avg(models.RagAnswerFeedback.accuracy_score).label("avg_accuracy_score"),
        func.avg(models.RagAnswerFeedback.grounding_score).label("avg_grounding_score"),
        func.avg(models.RagAnswerFeedback.source_relevance_score).label("avg_source_relevance_score"),
        func.avg(models.RagAnswerFeedback.helpfulness_score).label("avg_helpfulness_score"),
    )
    
    if user_name:
        query = query.filter(models.RagAnswerFeedback.user_name == user_name)
        
    if subject:
        query = query.filter(models.RagAnswerFeedback.subject == subject)
    
    result = query.first()
    
    if result.feedback_count == 0:
        return {
            "feedback_count": 0,
            "message": "아직 RAG 답변 평가 데이터가 없습니다.",
        }
        
    return {
        "feedback_count": result.feedback_count,
        "avg_accuracy_score": round(float(result.avg_accuracy_score), 2),
        "avg_grounding_score": round(float(result.avg_grounding_score), 2),
        "avg_score_relevance_score": round(float(result.avg_score_relevance_score), 2),
        "avg_helpfulness_score": round(float(result.avg_helpfulness_score), 2),
    }
    
    
@router.get("/recent")
def get_recent_rag_feedback(
    user_name: str | None = None,
    subject: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(models.RagAnswerFeedback)
    
    if user_name:
        query = query.filter(models.RagAnswerFeedback.user_name == user_name)
        
    if subject:
        query = query.filter(models.RagAnswerFeedback.subject == subject)
        
    feedback_items = (
        query.order_by(models.RagAnswerFeedback.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": item.id,
            "user_name": item.user_name,
            "subject": item.subject,
            "material_id": item.material_id,
            "question": item.question,
            "accuracy_score": item.accuracy_score,
            "grounding_score": item.grounding_score,
            "source_relevance_score": item.source_relevance_score,
            "helpfulness_score": item.helpfulness_score,
            "comment": item.comment,
            "created_at": item.created_at,
        }
        for item in feedback_items
    ]