from datetime import timedelta

from sqlalchemy.orm import Session

from app import models
from app.ai import recommendation_ai
from app.time_utils import utc_now
from app.services.exceptions import (
    InvalidAIResponseError,
    InvalidRequestError,
    ResourceNotFoundError,
)
from app.services.analytics import metrics_service


def generate_and_save_queue(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    subject: str | None = None,
    limit: int,
):
    if limit <= 0 or limit > 10:
        raise InvalidRequestError(
            "limit은 1 이상 10 이하이어야 합니다."
        )
        
    weak_concepts = metrics_service.get_weak_concepts_from_wrong_answers(
        db=db,
        user_id=user_id,
        subject=subject,
        limit=limit,
    )
    
    recent_wrong_query = (
        db.query(models.WrongAnswer)
        .filter(models.WrongAnswer.user_id == user_id)
    )

    if subject:
        recent_wrong_query = (
            recent_wrong_query.join(
                models.Question,
                models.WrongAnswer.question_id == models.Question.id,
            )
            .join(
                models.StudyMaterial,
                models.Question.material_id == models.StudyMaterial.id,
            )
            .filter(models.StudyMaterial.subject == subject)
        )

    recent_wrong_query = (
        recent_wrong_query.order_by(models.WrongAnswer.created_at.desc())
        .limit(10)
    )
    
    recent_wrong_answers = recent_wrong_query.all()
    
    recent_wrong_data = [
        {
            "id": item.id,
            "question_id": item.question_id,
            "concept": item.concept,
            "user_answer": item.user_answer,
            "correct_answer": item.correct_answer,
            "created_at": str(item.created_at),
        }
        for item in recent_wrong_answers
    ]
    
    checklist_query = (
        db.query(models.StudyChecklistItem)
        .filter(models.StudyChecklistItem.user_id == user_id)
        .filter(models.StudyChecklistItem.is_done == False)
    )
    
    if subject:
        checklist_query = checklist_query.filter(
            models.StudyChecklistItem.subject == subject
        )
        
    pending_checklists = (
        checklist_query.order_by(
            models.StudyChecklistItem.priority.asc(),
            models.StudyChecklistItem.created_at.desc(),
        )
        .limit(10)
        .all()
    )
    
    pending_checklist_data = [
        {
            "id": item.id,
            "subject": item.subject,
            "title": item.title,
            "description": item.description,
            "priority": item.priority,
        }
        for item in pending_checklists
    ]
    
    since = utc_now() - timedelta(days=7)
    
    session_query = (
        db.query(models.StudySession)
        .filter(models.StudySession.user_id == user_id)
        .filter(models.StudySession.created_at >= since)
    )
    
    if subject:
        session_query = session_query.filter(
            models.StudySession.subject == subject
        )
        
    sessions = session_query.all()
    
    session_result = metrics_service.build_session_summary(
        sessions=sessions
    )
    
    session_summary = {
        "period_days": 7,
        **session_result,
    }
    
    attempt_query = (
        db.query(models.ExamAttempt)
        .filter(models.ExamAttempt.user_id == user_id)
        .filter(models.ExamAttempt.created_at >= since)
    )
    
    if subject:
        attempt_query = attempt_query.filter(
            models.ExamAttempt.subject == subject
        )
        
    attempts = attempt_query.order_by(models.ExamAttempt.created_at.desc()).all()
    
    attempt_summary = {
        "period_days": 7,
        "attempt_count": len(attempts),
        "avg_score": round(sum(attempt.score for attempt in attempts) / len(attempts), 2)
        if attempts
        else None,
        "latest_score": attempts[0].score if attempts else None,
    }
    
    has_any_data = bool(
        weak_concepts
        or recent_wrong_data
        or pending_checklist_data
        or sessions
        or attempts
    )
    
    if not has_any_data:
        raise ResourceNotFoundError(
            "스마트 복습 큐를 생성할 학습 데이터가 없습니다."
        )
        
    generated_items = recommendation_ai.generate_smart_review_queue_items(
        user_name=user_name,
        subject=subject,
        weak_concepts=weak_concepts,
        recent_wrong_answers=recent_wrong_data,
        pending_checklists=pending_checklist_data,
        session_summary=session_summary,
        attempt_summary=attempt_summary,
        limit=limit,
    )
    generated_items = _validate_generated_items(
        generated_items,
        limit=limit,
    )
    
    saved_items = []
    
    try:
        for item in generated_items:
            queue_item = models.SmartReviewQueueItem(
                user_id=user_id,
                subject=subject,
                title=item.get("title", ""),
                reason=item.get("reason", ""),
                action=item.get("action", ""),
                estimated_minutes=item.get("estimated_minutes"),
                priority=item.get("priority", 1),
                source_type=item.get("source_type"),
                is_done=False,
            )
            
            db.add(queue_item)
            saved_items.append(queue_item)
            
        db.commit()
        
        for item in saved_items:
            db.refresh(item)
            
    except Exception:
        db.rollback()
        raise
        
    return {
        "item_count": len(saved_items),
        "items": saved_items,
    }
    

def list_queue_items(
    db: Session,
    *,
    user_id: int,
    subject: str | None = None,
    include_done: bool = True,
    limit: int,
):
    query = (
        db.query(models.SmartReviewQueueItem)
        .filter(models.SmartReviewQueueItem.user_id == user_id)
    )
    
    if subject:
        query = query.filter(models.SmartReviewQueueItem.subject == subject)
        
    if not include_done:
        query = query.filter(models.SmartReviewQueueItem.is_done == False)
        
    items = (
        query.order_by(
            models.SmartReviewQueueItem.is_done.asc(),
            models.SmartReviewQueueItem.priority.asc(),
            models.SmartReviewQueueItem.created_at.desc(),
        )
        .limit(limit)
        .all()
    )
    
    total_count = len(items)
    done_count = sum(1 for item in items if item.is_done)
    progress_rate = round((done_count / total_count) * 100, 2) if total_count else 0
    
    return {
        "total_count": total_count,
        "done_count": done_count,
        "progress_rate": progress_rate,
        "items": [
            {
                "id": item.id,
                "subject": item.subject,
                "title": item.title,
                "reason": item.reason,
                "action": item.action,
                "estimated_minutes": item.estimated_minutes,
                "priority": item.priority,
                "source_type": item.source_type,
                "is_done": item.is_done,
                "created_at": item.created_at,
                "completed_at": item.completed_at,
            }
            for item in items
        ],
    }
    

def update_queue_item(
    db: Session,
    *,
    user_id: int,
    item_id: int,
    is_done: bool,
):
    item = (
        db.query(models.SmartReviewQueueItem)
        .filter(models.SmartReviewQueueItem.id == item_id)
        .filter(models.SmartReviewQueueItem.user_id == user_id)
        .first()
    )
    
    if item is None:
        raise ResourceNotFoundError(
            "스마트 복습 큐 항목을 찾지 못했습니다."
        )
        
    item.is_done = is_done
    item.completed_at = utc_now() if is_done else None

    try:
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        raise
    
    return {
        "item": {
            "id": item.id,
            "subject": item.subject,
            "title": item.title,
            "reason": item.reason,
            "action": item.action,
            "estimated_minutes": item.estimated_minutes,
            "priority": item.priority,
            "source_type": item.source_type,
            "is_done": item.is_done,
            "created_at": item.created_at,
            "completed_at": item.completed_at,
        },
    }


def _validate_generated_items(generated_items, *, limit: int) -> list[dict]:
    if not isinstance(generated_items, list) or not generated_items:
        raise InvalidAIResponseError(
            "AI가 생성한 스마트 복습 항목 형식이 올바르지 않습니다."
        )

    validated_items = []

    for item in generated_items[:limit]:
        if not isinstance(item, dict):
            raise InvalidAIResponseError(
                "AI가 생성한 스마트 복습 항목 형식이 올바르지 않습니다."
            )

        title = item.get("title")
        reason = item.get("reason", "")
        action = item.get("action", "")
        estimated_minutes = item.get("estimated_minutes")
        priority = item.get("priority", 1)
        source_type = item.get("source_type")

        if not isinstance(title, str) or not title.strip():
            raise InvalidAIResponseError(
                "AI가 생성한 스마트 복습 항목 제목이 올바르지 않습니다."
            )
        if not isinstance(reason, str) or not isinstance(action, str):
            raise InvalidAIResponseError(
                "AI가 생성한 스마트 복습 항목 설명이 올바르지 않습니다."
            )
        if (
            estimated_minutes is not None
            and (
                isinstance(estimated_minutes, bool)
                or not isinstance(estimated_minutes, int)
                or estimated_minutes <= 0
            )
        ):
            raise InvalidAIResponseError(
                "AI가 생성한 예상 학습 시간이 올바르지 않습니다."
            )
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 1:
            raise InvalidAIResponseError(
                "AI가 생성한 스마트 복습 우선순위가 올바르지 않습니다."
            )
        if source_type is not None and not isinstance(source_type, str):
            raise InvalidAIResponseError(
                "AI가 생성한 스마트 복습 출처 형식이 올바르지 않습니다."
            )

        validated_items.append(
            {
                "title": title.strip(),
                "reason": reason,
                "action": action,
                "estimated_minutes": estimated_minutes,
                "priority": priority,
                "source_type": source_type,
            }
        )

    return validated_items
