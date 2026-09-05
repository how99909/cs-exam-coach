from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas, models
from app.database import get_db
from app.dependencies import get_current_user
from app.services.feedback import rag_feedback_service
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError

router = APIRouter(prefix="/rag-feedback", tags=["rag-feedback"])


@router.post("/answer")
def create_rag_answer_feedback(
    request: schemas.RagAnswerFeedbackCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = rag_feedback_service.create_feedback(
            db=db,
            user_id=current_user.id,
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

    except InvalidRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    
    return {
        "success": True,
        "message": "RAG 답변 평가가 저장되었습니다.",
        **result,
    }
    
    
@router.get("/summary")
def get_rag_feedback_summary(
    subject: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = rag_feedback_service.get_summary(
        db=db,
        user_id=current_user.id,
        subject=subject,
    )
        
    return result
    
    
@router.get("/recent")
def get_recent_rag_feedback(
    subject: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = rag_feedback_service.get_recent(
        db=db,
        user_id=current_user.id,
        user_name=current_user.user_name,
        subject=subject,
        limit=limit,
    )
    
    return result
