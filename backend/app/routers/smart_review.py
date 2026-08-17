from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import ai_service, models, schemas
from app.database import get_db

router = APIRouter(prefix="/smart-review", tags=["smart-review"])

@router.post("/queue/save")
def save_smart_review_queue(
    request: schemas.SmartReviewQueueRequest,
    db: Session = Depends(get_db),
):
    if request.limit <= 0 or request.limit > 10:
        raise HTTPException(
            status_code=400,
            detail="limit은 1 이상 10 이하이어야 합니다.",
        )
        
    wrong_query = (
        db.query(
            models.WrongAnswer.concept,
            func.count(models.WrongAnswer.id).label("wrong_count"),
        )
        .filter(models.WrongAnswer.user_name == request.user_name)
        .filter(models.WrongAnswer.concept.isnot(None))
        .filter(models.WrongAnswer.concept != "")
    )

    if request.subject:
        wrong_query = (
            wrong_query
            .join(models.Question, models.WrongAnswer.question_id == models.Question.id)
            .join(models.StudyMaterial, models.Question.material_id == models.StudyMaterial.id)
            .filter(models.StudyMaterial.subject == request.subject)
        )
        
    weak_rows = (
        wrong_query
        .group_by(models.WrongAnswer.concept)
        .order_by(func.count(models.WrongAnswer.id).desc())
        .limit(10)
        .all()
    )
    
    weak_concepts = [
        {
            "concept": row.concept,
            "wrong_count": row.wrong_count,
        }
        for row in weak_rows
    ]
    
    recent_wrong_query = (
        db.query(models.WrongAnswer)
        .filter(models.WrongAnswer.user_name == request.user_name)
        .order_by(models.WrongAnswer.created_at.desc())
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
        .filter(models.StudyChecklistItem.user_name == request.user_name)
        .filter(models.StudyChecklistItem.is_done == False)
    )
    
    if request.subject:
        checklist_query = checklist_query.filter(
            models.StudyChecklistItem.subject == request.subject
        )
        
    pending_checklists = (
        checklist_query
        .order_by(
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
    
    since = datetime.utcnow() - timedelta(days=7)
    
    session_query = (
        db.query(models.StudySession)
        .filter(models.StudySession.user_name == request.user_name)
        .filter(models.StudySession.created_at >= since)
    )
    
    if request.subject:
        session_query = session_query.filter(
            models.StudySession.subject == request.subject
        )
        
    sessions = session_query.all()
    
    total_minutes = sum(session.duration_minutes for session in sessions)
    focus_scores = [
        session.focus_score
        for session in sessions
        if session.focus_score is not None
    ]
    
    session_summary = {
        "period_days": 7,
        "session_count": len(sessions),
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 2),
        "avg_focus_score": round(sum(focus_scores) / len(focus_scores), 2)
        if focus_scores
        else None,
    }
    
    attempt_query = (
        db.query(models.ExamAttempt)
        .filter(models.ExamAttempt.user_name == request.user_name)
        .filter(models.ExamAttempt.created_at >= since)
    )
    
    if request.subject:
        attempt_query = attempt_query.filter(
            models.ExamAttempt.subject == request.subject
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
        raise HTTPException(
            status_code=404,
            detail="스마트 복습 큐를 생성할 학습 데이터가 없습니다.",
        )
        
    generated_items = ai_service.generate_smart_review_queue_items(
        user_name=request.user_name,
        subject=request.subject,
        weak_concepts=weak_concepts,
        recent_wrong_answers=recent_wrong_data,
        pending_checklists=pending_checklist_data,
        session_summary=session_summary,
        attempt_summary=attempt_summary,
        limit=request.limit,
    )
    
    saved_items = []
    
    for item in generated_items:
        queue_item = models.SmartReviewQueueItem(
            user_name=request.user_name,
            subject=request.subject,
            title=item.get("title", ""),
            reason=item.get("reason", ""),
            action=item.get("action", ""),
            estimated_minutes=item.get("estimated_minutes"),
            priority=item.get("priority", 1),
            source_type=item.get("source_type"),
            is_done=False,
        )
        
        db.add(queue_item)
        db.commit()
        db.refresh(queue_item)
        
        saved_items.append(
            {
                "id": queue_item.id,
                "subject": queue_item.subject,
                "title": queue_item.title,
                "reason": queue_item.reason,
                "action": queue_item.action,
                "estimated_minutes": queue_item.estimated_minutes,
                "priority": queue_item.priority,
                "source_type": queue_item.source_type,
                "is_done": queue_item.is_done,
                "created_at": queue_item.created_at,
                "completed_at": queue_item.completed_at,
            }
        )
        
    return {
        "success": True,
        "message": "스마트 복습 큐가 저장되었습니다.",
        "item_count": len(saved_items),
        "items": saved_items,
    }
    
    
@router.get("/queue/items")
def list_smart_review_queue_items(
    user_name: str,
    subject: str | None = None,
    include_done: bool = True,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.SmartReviewQueueItem).filter(
        models.SmartReviewQueueItem.user_name == user_name
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
        "success": True,
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
    
    
@router.patch("/queue/items/{item_id}")
def update_smart_review_queue_item(
    item_id: int,
    request: schemas.SmartReviewQueueUpdateRequest,
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.SmartReviewQueueItem)
        .filter(models.SmartReviewQueueItem.id == item_id)
        .filter(models.SmartReviewQueueItem.user_name == request.user_name)
        .first()
    )
    
    if item is None:
        raise HTTPException(
            status_code=404,
            detail="스마트 복습 큐 항목을 찾지 못했습니다.",
        )
        
    item.is_done = request.is_done
    item.completed_at = datetime.utcnow() if request.is_done else None
    
    db.commit()
    db.refresh(item)
    
    return {
        "success": True,
        "message": "스마트 복습 큐 항목 상태가 변경되었습니다.",
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
