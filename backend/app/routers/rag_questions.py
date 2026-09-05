from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.services.rag import question_service
from app.database import get_db
from app.dependencies import get_current_user
from app.services.exceptions import ResourceNotFoundError

router = APIRouter(prefix="/rag-questions", tags=["rag-questions"])


@router.post("/generate")
def generate_rag_based_questions(
    request: schemas.RagQuestionGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):      
    try:
        result = question_service.generate_rag_questions(
            db=db,
            user_id=current_user.id,
            user_name=current_user.user_name,
            subject=request.subject,
            material_id=request.material_id,
            question_type=request.question_type,
            difficulty=request.difficulty,
            count=request.count,
            top_k=request.top_k,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="RAG 기반 예상문제 생성 중 오류가 발생했습니다.",
        ) from exc

    return {
        "success": True,
        "message": "RAG 기반 예상문제가 생성되었습니다.",
        **result,
    }
