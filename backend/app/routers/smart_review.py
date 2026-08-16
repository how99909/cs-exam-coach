from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import ai_service, models, schemas
from app.database import get_db

router = APIRouter(prefix="/smart-review", tags=["smart-review"])

@router.post("/queue")
def generate_smart_review_queue(
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
        
    queue = ai_service.generate_smart_review_queue(
        user_name=request.user_name,
        subject=request.subject,
        weak_concepts=weak_concepts,
        recent_wrong_answers=recent_wrong_data,
        pending_checklists=pending_checklist_data,
        session_summary=session_summary,
        attempt_summary=attempt_summary,
        limit=request.limit,
    )
    
    return {
        "success": True,
        "message": "스마트 복습 큐가 생성되었습니다.",
        "weak_concepts": weak_concepts,
        "recent_wrong_answers": recent_wrong_data,
        "pending_checklists": pending_checklist_data,
        "session_summary": session_summary,
        "attempt_summary": attempt_summary,
        "queue": queue,
    }