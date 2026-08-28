from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import ai_service, models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.time_utils import utc_now

router = APIRouter(prefix="/weekly-reports", tags=["weekly-reports"])


@router.post("/generate")
def generate_weekly_report(
    request: schemas.WeeklyStudyReportRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if request.days > 31:
        raise HTTPException(
            status_code=400,
            detail="days는 1 이상 31 이하이어야 합니다.",
        )
        
    end_at = utc_now()
    start_at = end_at - timedelta(days=request.days)
    
    session_query = db.query(models.StudySession).filter(
        models.StudySession.user_id == current_user.id
    ).filter(
        models.StudySession.created_at >= start_at
    )
    
    if request.subject:
        session_query = session_query.filter(
            models.StudySession.subject == request.subject
        )
        
    sessions = session_query.all()
    
    total_minutes = sum(session.duration_minutes for session in sessions)
    total_hours = round(total_minutes / 60, 2)
    
    focus_scores = [
        session.focus_score
        for session in sessions
        if session.focus_score is not None
    ]
    
    avg_focus_score = (
        round(sum(focus_scores) / len(focus_scores), 2)
        if focus_scores 
        else None
    )
    
    session_summary = {
        "session_count": len(sessions),
        "total_minutes": total_minutes,
        "total_hours": total_hours,
        "avg_focus_score": avg_focus_score,
    }
    
    attempt_query = db.query(models.ExamAttempt).filter(
        models.ExamAttempt.user_id == current_user.id
    ).filter(
        models.ExamAttempt.created_at >= start_at
    )
    
    if request.subject:
        attempt_query = attempt_query.filter(
            models.ExamAttempt.subject == request.subject
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
                "subject":attempt.subject,
                "score": attempt.score,
                "created_at": str(attempt.created_at),
            }
            for attempt in reversed(attempts)
        ],
    }
    
    attempt_ids = [attempt.id for attempt in attempts]
    
    weak_concepts = []
    
    if attempt_ids:
        weak_rows = (
            db.query(
                models.Question.concept,
                func.count(models.ExamAttemptAnswer.id).label("wrong_count"),
            )
            .join(
                models.ExamAttemptAnswer,
                models.ExamAttemptAnswer.question_id == models.Question.id,
            )
            .filter(models.ExamAttemptAnswer.attempt_id.in_(attempt_ids))
            .filter(models.ExamAttemptAnswer.is_correct == False)
            .filter(models.Question.concept.isnot(None))
            .filter(models.Question.concept != "")
            .group_by(models.Question.concept)
            .order_by(func.count(models.ExamAttemptAnswer.id).desc())
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
        
    checklist_query = db.query(models.StudyChecklistItem).filter(
        models.StudyChecklistItem.user_id == current_user.id
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
        "progress_rate": checklist_progress_rate,
        "pending_count": checklist_total - checklist_done,
    }
    
    period_summary = {
        "days": request.days,
        "start_at": str(start_at),
        "end_at": str(end_at),
    }
    
    has_any_data = bool(sessions or attempts or checklist_items)
    
    if not has_any_data:
        raise HTTPException(
            status_code=404,
            detail="주간 리포트를 생성할 학습 데이터가 없습니다.",
        )
        
    report = ai_service.generate_weekly_study_report(
        user_name=current_user.user_name,
        subject=request.subject,
        period_summary=period_summary,
        session_summary=session_summary,
        attempt_summary=attempt_summary,
        weak_concepts=weak_concepts,
        checklist_summary=checklist_summary,
    )
    
    return {
        "success": True,
        "message": "주간 학습 리포트가 생성되었습니다",
        "period_summary": period_summary,
        "session_summary": session_summary,
        "attempt_summary": attempt_summary,
        "weak_concepts": weak_concepts,
        "checklist_summary": checklist_summary,
        "report": report,
    }
