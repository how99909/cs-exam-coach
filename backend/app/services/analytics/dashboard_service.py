from typing import Any
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app import models
from app.ai import dashboard_ai
from app.services.analytics import metrics_service
from app.services.exceptions import ResourceNotFoundError
from app.time_utils import utc_now


def get_goal_dashboard(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    goal_id: int,
) -> dict[str, Any]:
    goal = (
        db.query(models.StudyGoal)
        .filter(models.StudyGoal.id == goal_id)
        .filter(models.StudyGoal.user_id == user_id)
        .first()
    )
    
    if goal is None:
        raise ResourceNotFoundError(
            "학습 목표를 찾지 못했습니다."
        )
        
    days_left = (goal.exam_date - date.today()).days
    
    checklist_items = (
        db.query(models.StudyChecklistItem)
        .filter(models.StudyChecklistItem.user_id == user_id)
        .filter(models.StudyChecklistItem.goal_id == goal.id)
        .all()
    )
    
    checklist_summary = metrics_service.build_checklist_summary(
        items=checklist_items
    )
    
    sessions = (
        db.query(models.StudySession)
        .filter(models.StudySession.user_id == user_id)
        .filter(models.StudySession.goal_id == goal.id)
        .order_by(models.StudySession.created_at.desc())
        .all()
    )
    
    session_summary = metrics_service.build_session_summary(
        sessions=sessions
    )
    session_summary["recent_sessions"] = [
        {
            "id": session.id,
            "duration_minutes": session.duration_minutes,
            "content": session.content,
            "reflection": session.reflection,
            "focus_score": session.focus_score,
            "created_at": session.created_at,
        }
        for session in sessions[:5]
    ]
    
    attempts = (
        db.query(models.ExamAttempt)
        .filter(models.ExamAttempt.user_id == user_id)
        .filter(models.ExamAttempt.subject == goal.subject)
        .order_by(models.ExamAttempt.created_at.desc())
        .limit(10)
        .all()
    )
    
    if attempts:
        avg_score = round(
            sum(attempt.score for attempt in attempts) / len(attempts),
            2,
        )
        latest_score = attempts[0].score
        best_score = max(attempt.score for attempt in attempts)
        score_gap = goal.target_score - avg_score
    else:
        avg_score = None
        latest_score = None
        best_score = None
        score_gap = None
        
    attempt_summary = {
        "attempt_count": len(attempts),
        "avg_score": avg_score,
        "latest_score": latest_score,
        "best_score": best_score,
        "target_score": goal.target_score,
        "score_gap": score_gap,
        "recent_attempts": [
            {
                "id": attempt.id,
                "title": attempt.title,
                "score": attempt.score,
                "correct_count": attempt.correct_count,
                "total_questions": attempt.total_questions,
                "created_at": attempt.created_at,
            }
            for attempt in attempts
        ],
    }
    
    attempt_ids = [attempt.id for attempt in attempts]
    
    weak_concepts = metrics_service.get_weak_concepts_from_attempts(
        db=db,
        attempt_ids=attempt_ids,
        limit=10,
    )
        
    goal_data = {
        "id": goal.id,
        "subject": goal.subject,
        "title": goal.title,
        "target_score": goal.target_score,
        "exam_date": goal.exam_date,
        "days_left": days_left,
        "created_at": goal.created_at,
    }
    
    comment = dashboard_ai.generate_goal_dashboard_comment(
        user_name=user_name,
        goal=goal_data,
        checklist_summary=checklist_summary,
        session_summary=session_summary,
        attempt_summary=attempt_summary,
        weak_concepts=weak_concepts,
    )
    
    return {
        "goal": goal_data,
        "checklist_summary": checklist_summary,
        "session_summary": session_summary,
        "attempt_summary": attempt_summary,
        "weak_concepts": weak_concepts,
        "comment": comment,
    }
    
    
def get_home_dashboard(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    subject: str | None,
) -> dict[str, Any]:
    since = utc_now() - timedelta(days=7)
    
    goal_query = db.query(models.StudyGoal).filter(
        models.StudyGoal.user_id == user_id
    )
    
    if subject:
        goal_query = goal_query.filter(models.StudyGoal.subject == subject)
        
    nearest_goal = (
        goal_query.filter(models.StudyGoal.exam_date >= date.today())
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
    
    session_summary = metrics_service.build_session_summary(
        sessions=sessions
    )
    session_summary["period_days"] = 7
    
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
        "best_score": max(attempt.score for attempt in attempts) if attempts else None,
    }
    
    queue_query = (
        db.query(models.SmartReviewQueueItem)
        .filter(models.SmartReviewQueueItem.user_id == user_id)
    )
    
    if subject:
        queue_query = queue_query.filter(
            models.SmartReviewQueueItem.subject == subject
        )
        
    queue_items = queue_query.all()
    result = metrics_service.build_checklist_summary(
        items=queue_items
    )
    
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
        **result,
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

    checklist_query = (
        db.query(models.StudyChecklistItem)
        .filter(models.StudyChecklistItem.user_id == user_id)
    )

    if subject:
        checklist_query = checklist_query.filter(
            models.StudyChecklistItem.subject == subject
        )

    checklist_items = checklist_query.all()
    
    checklist_summary = metrics_service.build_checklist_summary(
        items=checklist_items
    )

    weak_concepts = metrics_service.get_weak_concepts_from_wrong_answers(
        db=db,
        user_id=user_id,
        subject=subject,
        limit=5,
    )

    has_any_data = bool(
        goal_summary
        or sessions
        or attempts
        or queue_items
        or checklist_items
        or weak_concepts
    )

    if not has_any_data:
        raise ResourceNotFoundError(
            "홈 대시보드를 생성할 학습 데이터가 없습니다."
        )

    comment = dashboard_ai.generate_home_dashboard_comment(
        user_name=user_name,
        subject=subject,
        goal_summary=goal_summary,
        session_summary=session_summary,
        attempt_summary=attempt_summary,
        review_queue_summary=review_queue_summary,
        checklist_summary=checklist_summary,
        weak_concepts=weak_concepts,
    )

    return {
        "goal_summary": goal_summary,
        "session_summary": session_summary,
        "attempt_summary": attempt_summary,
        "review_queue_summary": review_queue_summary,
        "checklist_summary": checklist_summary,
        "weak_concepts": weak_concepts,
        "comment": comment,
    }
