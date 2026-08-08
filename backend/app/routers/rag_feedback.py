from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud_rag_feedback, schemas
from app.database import get_db

router = APIRouter(prefix="/rag-feedback", tags=["rag-feedback"])


def validate_score(score: int, field_name: str):
    if score < 1 or score > 5:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}는 1점 이상 5점 이하이어야 합니다.",
        )


@router.post("/answer")
def create_rag_answer_feedback(
    request: schemas.RagAnswerFeedbackCreate, 
    db: Session = Depends(get_db)
):
    validate_score(request.accuracy_score, "accuracy_score"),
    validate_score(request.grounding_score, "grounding_score"),
    validate_score(request.source_relevance_score, "source_relevance_score"),
    validate_score(request.helpfulness_score, "helpfulness_score"),
    
    feedback = crud_rag_feedback.create_rag_feedback(
        db=db,
        request=request,
    )
    
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
    result = crud_rag_feedback.get_rag_feedback_summary(
        db=db,
        user_name=user_name,
        subject=subject,
    )
    
    if result.feedback_count == 0:
        return {
            "feedback_count": 0,
            "message": "아직 RAG 답변 평가 데이터가 없습니다.",
        }
        
    return {
        "feedback_count": result.feedback_count,
        "avg_accuracy_score": round(float(result.avg_accuracy_score), 2),
        "avg_grounding_score": round(float(result.avg_grounding_score), 2),
        "avg_source_relevance_score": round(
            float(result.avg_source_relevance_score),
            2
        ),
        "avg_helpfulness_score": round(float(result.avg_helpfulness_score), 2),
    }
    
    
@router.get("/recent")
def get_recent_rag_feedback(
    user_name: str | None = None,
    subject: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    feedback_items = crud_rag_feedback.get_recent_rag_feedback(
        db=db,
        user_name=user_name,
        subject=subject,
        limit=limit,
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
