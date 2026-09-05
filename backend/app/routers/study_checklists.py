from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.services.study import checklist_service

router = APIRouter(prefix="/study-checklists", tags=["study-checklists"])


@router.post("/generate")
def generate_study_checklist(
    request: schemas.StudyChecklistGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        items = checklist_service.generate_checklist(
            db=db,
            user_id=current_user.id,
            user_name=current_user.user_name,
            goal_id=request.goal_id,
            item_count=request.item_count,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except InvalidRequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
        
    return {
        "success": True,
        "message": "학습 체크리스트가 생성되었습니다.",
        "item_count": len(items),
        "items": [_serialize_checklist_item(item) for item in items],
    }
    

@router.get("")
def list_study_checklist_items(
    goal_id: int | None = None,
    subject: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    items = checklist_service.list_checklist_items(
        db=db,
        user_id=current_user.id,
        goal_id=goal_id,
        subject=subject
    )
    
    summary = checklist_service.summarize_checklist_items(items)
    
    return {
        "success": True,
        **summary,
        "items": [_serialize_checklist_item(item) for item in items],
    }
    
    
@router.patch("/{item_id}")
def update_study_checklist_item(
    item_id: int,
    request: schemas.StudyChecklistUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        item = checklist_service.update_checklist_item(
            db=db,
            user_id=current_user.id,
            item_id=item_id,
            is_done=request.is_done,
        )
        
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc
    
    return {
        "success": True,
        "message": "체크리스트 상태가 변경되었습니다.",
        "item": _serialize_checklist_item(item),
    }


def _serialize_checklist_item(item: models.StudyChecklistItem) -> dict:
    return {
        "id": item.id,
        "goal_id": item.goal_id,
        "subject": item.subject,
        "title": item.title,
        "description": item.description,
        "priority": item.priority,
        "is_done": item.is_done,
        "created_at": item.created_at,
        "completed_at": item.completed_at,
    }
