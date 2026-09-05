from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.recommendation import smart_review_service
from app.services.exceptions import (
    InvalidAIResponseError,
    InvalidRequestError,
    ResourceNotFoundError,
)

router = APIRouter(prefix="/smart-review", tags=["smart-review"])


@router.post("/queue/save")
def save_smart_review_queue(
    request: schemas.SmartReviewQueueRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = smart_review_service.generate_and_save_queue(
            db=db,
            user_id=current_user.id,
            user_name=current_user.user_name,
            subject=request.subject,
            limit=request.limit,
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
    except InvalidAIResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
        
    return {
        "success": True,
        "message": "스마트 복습 큐가 저장되었습니다.",
        **result,
    }
    
    
@router.get("/queue/items")
def list_smart_review_queue_items(
    subject: str | None = None,
    include_done: bool = True,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = smart_review_service.list_queue_items(
        db=db,
        user_id=current_user.id,
        subject=subject,
        include_done=include_done,
        limit=limit,
    )
    
    return {
        "success": True,
        **result,
    }
    
    
@router.patch("/queue/items/{item_id}")
def update_smart_review_queue_item(
    item_id: int,
    request: schemas.SmartReviewQueueUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = smart_review_service.update_queue_item(
            db=db,
            user_id=current_user.id,
            item_id=item_id,
            is_done=request.is_done,
        )
        
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    
    return {
        "success": True,
        "message": "스마트 복습 큐 항목 상태가 변경되었습니다.",
        **result,
    }
