from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import ai_service, models, schemas
from app.database import get_db

router = APIRouter(prefix="/home-dashboard", tags=["home-dashboard"])


@router.post("")
def get_home_dashboard(
    request: schemas.HomeDashboardRequest,
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=7)
    
    goal_query = db.query(models.StudyGoal).filter(
        models.StudyGoal.user_name == request.user_name
    )
    
    if request.subject:
        goal_query = goal_query.filter(models.StudyGoal.subject == request.subject)
        
    nearest_goal = (
        goal_query
        .filter(models.StudyGoal.exam_date >= date.today())
        .order_by(models.StudyGoal.exam_date.asc())
        .first()
    )
    
    if nearest_goal:
        goal_summary = {
            "id": nearest_goal.id,
            "subject": nearest_goal.subject,
            "title": nearest_goal.title,
            "target_score": nearest_goal.target_score,
            "exam_date": nearest_goal.exam_date,
            "days_left": (nearest_goal.exam_date - date.today()).days,
        }
    else:
        goal_summary = None
        
    session_query = db.query(models.StudySession).filter(
        models.StudySession.user_name == request.user_name
    ).filter(
        models.StudySession.created_at >= since
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
    
    attempt_query = db.query(models.ExamAttempt).filter(
        models.ExamAttempt.user_name == request.user_name
    ).filter(
        models.ExamAttempt.created_at >= since
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
        "best_score": max(attempt.score for attempt in attempts) if attempts else None,
    }
    
    queue_query = db.query(models.SmartReviewQueueItem).filter(
        models.SmartReviewQueueItem.user_name == request.user_name
    )
    
    if request.subject:
        queue_query = queue_query.filter(
            models.SmartReviewQueueItem.subject == request.subject
        )
        
    queue_items = queue_query.all()
    
    queue_total = len(queue_items)
    queue_done = sum(1 for item in queue_items if item.is_done)
    queue_progress_rate = round((queue_done / queue_total) * 100, 2) if queue_total else 0
    
    recent_pending_queue = (
        queue_query
        .filter(models.SmartReviewQueueItem.is_done == False)
        .order_by(
            models.SmartReviewQueueItem.priority.asc(),
            models.SmartReviewQueueItem.created_at.desc(),
        )
        .limit(5)
        .all()
    )

    review_queue_summary = {
        "total_count": queue_total,
        "done_count": queue_done,
        "pending_count": queue_total - queue_done,
        "progress_rate": queue_progress_rate,
        "pending_items": [
            {
                "id": item.id,
                "title": item.title,
                "priority": item.priority,
                "estimated_minutes": item.estimated_minutes,
                "source_type": item.source_type,
            }
            for item in recent_pending_queue
        ],
    }

    checklist_query = db.query(models.StudyChecklistItem).filter(
        models.StudyChecklistItem.user_name == request.user_name
    )

    if request.subject:
        checklist_query = checklist_query.filter(
            models.StudyChecklistItem.subject == request.subject
        )

    checklist_items = checklist_query.all()

    checklist_total = len(checklist_items)
    checklist_done = sum(1 for item in checklist_items if item.is_done)
    checklist_progress_rate = (
        round((checklist_done / checklist_total) * 100, 2)
        if checklist_total
        else 0
    )

    checklist_summary = {
        "total_count": checklist_total,
        "done_count": checklist_done,
        "pending_count": checklist_total - checklist_done,
        "progress_rate": checklist_progress_rate,
    }

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
        .limit(5)
        .all()
    )

    weak_concepts = [
        {
            "concept": row.concept,
            "wrong_count": row.wrong_count,
        }
        for row in weak_rows
    ]

    has_any_data = bool(
        goal_summary
        or sessions
        or attempts
        or queue_items
        or checklist_items
        or weak_concepts
    )

    if not has_any_data:
        raise HTTPException(
            status_code=404,
            detail="홈 대시보드를 생성할 학습 데이터가 없습니다.",
        )

    comment = ai_service.generate_home_dashboard_comment(
        user_name=request.user_name,
        subject=request.subject,
        goal_summary=goal_summary,
        session_summary=session_summary,
        attempt_summary=attempt_summary,
        review_queue_summary=review_queue_summary,
        checklist_summary=checklist_summary,
        weak_concepts=weak_concepts,
    )

    return {
        "success": True,
        "message": "홈 대시보드가 생성되었습니다.",
        "goal_summary": goal_summary,
        "session_summary": session_summary,
        "attempt_summary": attempt_summary,
        "review_queue_summary": review_queue_summary,
        "checklist_summary": checklist_summary,
        "weak_concepts": weak_concepts,
        "comment": comment,
    }