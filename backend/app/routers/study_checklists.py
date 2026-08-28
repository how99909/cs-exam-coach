from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import ai_service, models, schemas
from app.database import get_db
from app.routers.study_goals import _get_study_goal_status
from app.dependencies import get_current_user
from app.time_utils import utc_now

router = APIRouter(prefix="/study-checklists", tags=["study-checklists"])


@router.post("/generate")
def generate_study_checklist(
    request: schemas.StudyChecklistGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    status_result = _get_study_goal_status(
        goal_id=request.goal_id,
        user_id=current_user.id,
        db=db,
    )
    
    goal = status_result["goal"]
    current_status = status_result["current_status"]
    weak_concepts = status_result["weak_concepts"]
    
    generated_items = ai_service.generate_study_checklist_items(
        user_name=current_user.user_name,
        goal=goal,
        current_status=current_status,
        weak_concepts=weak_concepts,
        item_count=request.item_count,
    )
    
    saved_items = []
    
    for item in generated_items:
        checklist_item = models.StudyChecklistItem(
            user_id=current_user.id,
            goal_id=request.goal_id,
            subject=goal["subject"],
            title=item.get("title", ""),
            description=item.get("description", ""),
            priority=item.get("priority", 1),
            is_done=False,
        )
        
        db.add(checklist_item)
        db.commit()
        db.refresh(checklist_item)
        
        saved_items.append(
            {
                "id": checklist_item.id,
                "goal_id": checklist_item.goal_id,
                "subject": checklist_item.subject,
                "title": checklist_item.title,
                "description": checklist_item.description,
                "priority": checklist_item.priority,
                "is_done": checklist_item.is_done,
                "created_at": checklist_item.created_at,
                "completed_at": checklist_item.completed_at,
            }
        )
        
    return {
        "success": True,
        "message": "학습 체크리스트가 생성되었습니다.",
        "item_count": len(saved_items),
        "items": saved_items,
    }
    

@router.get("")
def list_study_checklist_items(
    goal_id: int | None = None,
    subject: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.StudyChecklistItem).filter(
        models.StudyChecklistItem.user_id == current_user.id
    )
    
    if goal_id is not None:
        query = query.filter(models.StudyChecklistItem.goal_id == goal_id)
        
    if subject:
        query = query.filter(models.StudyChecklistItem.subject == subject)
        
    items = (
        query.order_by(
            models.StudyChecklistItem.is_done.asc(),
            models.StudyChecklistItem.priority.asc(),
            models.StudyChecklistItem.created_at.desc(),
        )
        .all()
    )
    
    done_count = sum(1 for item in items if item.is_done)
    total_count = len(items)
    progress_rate = round((done_count / total_count) * 100, 2) if total_count else 0
    
    return {
        "success": True,
        "total_count": total_count,
        "done_count": done_count,
        "progress_rate": progress_rate,
        "items": [
            {
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
            for item in items
        ],
    }
    
    
@router.patch("/{item_id}")
def update_study_checklist_item(
    item_id: int,
    request: schemas.StudyChecklistUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = (
        db.query(models.StudyChecklistItem)
        .filter(models.StudyChecklistItem.id == item_id)
        .filter(models.StudyChecklistItem.user_id == current_user.id)
        .first()
    )
    
    if item is None:
        raise HTTPException(
            status_code=404,
            detail="체크리스트 항목을 찾지 못했습니다.",
        )
        
    item.is_done = request.is_done
    item.completed_at = utc_now() if request.is_done else None
    
    db.commit()
    db.refresh(item)
    
    return {
        "success": True,
        "message": "체크리스트 상대가 변경되었습니다.",
        "item": {
            "id": item.id,
            "goal_id": item.goal_id,
            "subject": item.subject,
            "title": item.title,
            "description": item.description,
            "priority": item.priority,
            "is_done": item.is_done,
            "created_at": item.created_at,
            "completed_at": item.completed_at,
        },
    }
