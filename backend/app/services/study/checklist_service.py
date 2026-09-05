from sqlalchemy.orm import Session

from app import models
from app.ai import study_ai
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.services.study import goal_service
from app.time_utils import utc_now


def generate_checklist(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    goal_id: int,
    item_count: int,
) -> list[models.StudyChecklistItem]:
    status = goal_service.get_goal_status(
        goal_id=goal_id,
        user_id=user_id,
        db=db,
    )
    
    goal = status["goal"]
    
    generated_items = study_ai.generate_study_checklist_items(
        user_name=user_name,
        goal=goal,
        current_status=status["current_status"],
        weak_concepts=status["weak_concepts"],
        item_count=item_count,
    )

    generated_items = _validate_generated_items(
        generated_items,
        item_count=item_count,
    )
    
    saved_items = []
    
    try:
        for item in generated_items:
            checklist_item = models.StudyChecklistItem(
                user_id=user_id,
                goal_id=goal_id,
                subject=goal["subject"],
                title=item.get("title", ""),
                description=item.get("description", ""),
                priority=item.get("priority", 1),
                is_done=False,
            )
            
            db.add(checklist_item)
            saved_items.append(checklist_item)
            
        db.commit()
        
        for item in saved_items:
            db.refresh(item)
            
    except Exception:
        db.rollback()
        raise
        
    return saved_items
    

def list_checklist_items(
    db: Session,
    *,
    user_id: int,
    goal_id: int | None = None,
    subject: str | None = None,
) -> list[models.StudyChecklistItem]:
    query = db.query(models.StudyChecklistItem).filter(
        models.StudyChecklistItem.user_id == user_id
    )
    
    if goal_id is not None:
        query = query.filter(models.StudyChecklistItem.goal_id == goal_id)
        
    if subject:
        query = query.filter(models.StudyChecklistItem.subject == subject)
        
    return (
        query
        .order_by(
            models.StudyChecklistItem.is_done.asc(),
            models.StudyChecklistItem.priority.asc(),
            models.StudyChecklistItem.created_at.desc(),
        )
        .all()
    )
    
    
def update_checklist_item(
    db: Session,
    *,
    user_id: int,
    item_id: int,
    is_done: bool,
) -> models.StudyChecklistItem:
    item = (
        db.query(models.StudyChecklistItem)
        .filter(models.StudyChecklistItem.id == item_id)
        .filter(models.StudyChecklistItem.user_id == user_id)
        .first()
    )
    
    if item is None:
        raise ResourceNotFoundError(
            "체크리스트 항목을 찾지 못했습니다."
        )
        
    item.is_done = is_done
    item.completed_at = utc_now() if is_done else None
    
    try:
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        raise
    
    return item


def summarize_checklist_items(
    items: list[models.StudyChecklistItem],
) -> dict:
    done_count = sum(1 for item in items if item.is_done)
    total_count = len(items)

    return {
        "total_count": total_count,
        "done_count": done_count,
        "progress_rate": (
            round((done_count / total_count) * 100, 2)
            if total_count
            else 0
        ),
    }


def _validate_generated_items(
    generated_items,
    *,
    item_count: int,
) -> list[dict]:
    if not isinstance(generated_items, list):
        raise InvalidRequestError(
            "AI가 생성한 체크리스트 형식이 올바르지 않습니다."
        )

    validated_items = []

    for item in generated_items[:item_count]:
        if not isinstance(item, dict):
            raise InvalidRequestError(
                "AI가 생성한 체크리스트 항목 형식이 올바르지 않습니다."
            )

        title = item.get("title")
        description = item.get("description", "")
        priority = item.get("priority", 1)

        if not isinstance(title, str) or not title.strip():
            raise InvalidRequestError(
                "AI가 생성한 체크리스트 제목이 올바르지 않습니다."
            )

        if not isinstance(description, str):
            raise InvalidRequestError(
                "AI가 생성한 체크리스트 설명이 올바르지 않습니다."
            )

        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 1:
            raise InvalidRequestError(
                "AI가 생성한 체크리스트 우선순위가 올바르지 않습니다."
            )

        validated_items.append(
            {
                "title": title.strip(),
                "description": description,
                "priority": priority,
            }
        )

    return validated_items
