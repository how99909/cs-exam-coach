from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.services.rag import question_service
from app.database import get_db
from app.dependencies import get_current_user
from app.services.exceptions import ResourceNotFoundError

router = APIRouter(
    prefix="/weakness-rag-questions",
    tags=["weakness-rag-questions"],
)

@router.post("/generate")
def generate_weakness_rag_questions(
    request: schemas.WeaknessRagQuestionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = question_service.generate_weakness_rag_questions(
            db=db,
            user_id=current_user.id,
            user_name=current_user.user_name,
            subject=request.subject,
            material_id=request.material_id,
            weakness_count=request.weakness_count,
            question_count=request.question_count,
            question_type=request.question_type,
            difficulty=request.difficulty,
            top_k_per_concept=request.top_k_per_concept,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="약점 기반 RAG 복습 문제 생성 중 오류가 발생했습니다.",
        ) from exc
        
    return {
        "success": True,
        "message": "약점 기반 RAG 복습 문제가 생성되었습니다.",
        **result,
    }
