from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services import exam_paper_service
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError

router = APIRouter(prefix="/exam-papers", tags=["exam-papers"])


@router.get("/questions")
def list_questions_for_exam_paper(
    subject: str,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = exam_paper_service.list_questions(
            db=db,
            user_id=current_user.id,
            subject=subject,
            limit=limit,
        )
    except InvalidRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    
    return {
        "success": True,
        **result,
    }
    
    
@router.post("/generate")
def generate_exam_paper(
    request: schemas.ExamPaperGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = exam_paper_service.generate_exam_paper(
            db=db,
            user_id=current_user.id,
            user_name=current_user.user_name,
            subject=request.subject,
            title=request.title,
            question_ids=request.question_ids,
            include_answers=request.include_answers,
            include_explanations=request.include_explanations,
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
        "message": "시험지가 생성되었습니다.",
        **result,
    }
