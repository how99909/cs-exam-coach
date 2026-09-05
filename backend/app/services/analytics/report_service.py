from datetime import timedelta
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models
from app.ai import report_ai
from app.services.analytics import metrics_service
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.time_utils import utc_now


def generate_personal_report(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    subject: str | None,
    limit: int,
) -> dict[str, Any]:
    query = (
        db.query(models.ExamAttempt)
        .filter(models.ExamAttempt.user_id == user_id)
    )
    
    if subject:
        query = query.filter(models.ExamAttempt.subject == subject)
        
    attempts = (
        query.order_by(models.ExamAttempt.created_at.desc())
        .limit(limit)
        .all()
    )
    
    if not attempts:
        raise ResourceNotFoundError(
            "학습 리포트를 생성할 응시 기록이 없습니다.",
        )
        
    scores = [
        attempt.score
        for attempt in attempts
    ]
    
    attempt_summary = {
        "attempt_count": len(attempts),
        "average_score": round(sum(scores) / len(scores), 2),
        "latest_score": attempts[0].score,
        "best_score": max(scores),
        "lowest_score": min(scores),
    }
    
    score_trend = [
        {
            "attempt_id": attempt.id,
            "title": attempt.title,
            "subject": attempt.subject,
            "score": attempt.score,
            "correct_count": attempt.correct_count,
            "total_questions": attempt.total_questions,
            "created_at": str(attempt.created_at),
        }
        for attempt in reversed(attempts)
    ]
    
    weak_concepts = (
        metrics_service.get_weak_concepts_from_attempts(
            db=db,
            attempt_ids=[
                attempt.id
                for attempt in attempts
            ],
            limit=10,
        )
    )
    
    report = report_ai.generate_study_report(
        user_name=user_name,
        subject=subject,
        attempt_summary=attempt_summary,
        weak_concepts=weak_concepts,
        score_trend=score_trend,
    )
    
    return {
        "attempt_summary": attempt_summary,
        "weak_concepts": weak_concepts,
        "score_trend": score_trend,
        "report": report,
    }
    
    
def generate_weekly_report(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    subject: str | None,
    days: int,
) -> dict[str, Any]:
    if not 1 <= days <= 31:
        raise InvalidRequestError("days는 1 이상 31 이하이어야 합니다.")

    end_at = utc_now()
    start_at = end_at - timedelta(days=days)
    
    session_query = (
        db.query(models.StudySession)
        .filter(models.StudySession.user_id == user_id)
        .filter(models.StudySession.created_at >= start_at)
    )
    if subject:
        session_query = session_query.filter(
            models.StudySession.subject == subject
        )
    sessions = session_query.all()
    session_summary = metrics_service.build_session_summary(
        sessions=sessions,
    )
    
    attempt_query = (
        db.query(models.ExamAttempt)
        .filter(models.ExamAttempt.user_id == user_id)
        .filter(models.ExamAttempt.created_at >= start_at)
    )
    if subject:
        attempt_query = attempt_query.filter(
            models.ExamAttempt.subject == subject
        )
    attempts = attempt_query.order_by(models.ExamAttempt.created_at.desc()).all()
    if attempts:
        avg_score = round(
            sum(attempt.score for attempt in attempts) / len(attempts),
            2,
        )
        latest_score = attempts[0].score
        best_score = max(attempt.score for attempt in attempts)
        lowest_score = min(attempt.score for attempt in attempts)
    else:
        avg_score = None
        latest_score = None
        best_score = None
        lowest_score = None
    attempt_summary = {
        "attempt_count": len(attempts),
        "avg_score": avg_score,
        "latest_score": latest_score,
        "best_score": best_score,
        "lowest_score": lowest_score,
        "score_trend": [
            {
                "attempt_id": attempt.id,
                "title": attempt.title,
                "subject": attempt.subject,
                "score": attempt.score,
                "created_at": str(attempt.created_at),
            }
            for attempt in reversed(attempts)
        ],
    }
    
    attempt_ids = [attempt.id for attempt in attempts]
    weak_concepts = metrics_service.get_weak_concepts_from_attempts(
        db=db,
        attempt_ids=attempt_ids,
        limit=10,
    )
        
    checklist_query = (
        db.query(models.StudyChecklistItem)
        .filter(models.StudyChecklistItem.user_id == user_id)
        .filter(
            or_(
                models.StudyChecklistItem.created_at >= start_at,
                models.StudyChecklistItem.completed_at >= start_at,
            )
        )
    )
    if subject:
        checklist_query = checklist_query.filter(
            models.StudyChecklistItem.subject == subject
        )
    checklist_items = checklist_query.all()
    checklist_summary = metrics_service.build_checklist_summary(
        items=checklist_items
    )
    
    period_summary = {
        "days": days,
        "start_at": str(start_at),
        "end_at": str(end_at),
    }
    
    has_any_data = bool(sessions or attempts or checklist_items)
    
    if not has_any_data:
        raise ResourceNotFoundError(
            "주간 리포트를 생성할 학습 데이터가 없습니다."
        )
        
    report = report_ai.generate_weekly_study_report(
        user_name=user_name,
        subject=subject,
        period_summary=period_summary,
        session_summary=session_summary,
        attempt_summary=attempt_summary,
        weak_concepts=weak_concepts,
        checklist_summary=checklist_summary,
    )
    
    return {
        "period_summary": period_summary,
        "session_summary": session_summary,
        "attempt_summary": attempt_summary,
        "weak_concepts": weak_concepts,
        "checklist_summary": checklist_summary,
        "report": report,
    }
