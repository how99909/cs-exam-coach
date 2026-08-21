from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import ai_service, models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/goal-dashboard", tags=["goal-dashboard"])


@router.post("")
def get_goal_dashboard(
    request: schemas.GoalDashboardRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goal = (
        db.query(models.StudyGoal)
        .filter(models.StudyGoal.id == request.goal_id)
        .filter(models.StudyGoal.user_name == current_user.user_name)
        .first()
    )
    
    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="학습 목표를 찾지 못했습니다.",
        )
        
    days_left = (goal.exam_date - date.today()).days
    
    checklist_items = (
        db.query(models.StudyChecklistItem)
        .filter(models.StudyChecklistItem.user_name == current_user.user_name)
        .filter(models.StudyChecklistItem.goal_id == goal.id)
        .all()
    )
    
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
    
    sessions = (
        db.query(models.StudySession)
        .filter(models.StudySession.user_name == current_user.user_name)
        .filter(models.StudySession.goal_id == goal.id)
        .order_by(models.StudySession.created_at.desc())
        .all()
    )
    
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
        "recent_sessions": [
            {
                "id": session.id,
                "duration_minutes": session.duration_minutes,
                "content": session.content,
                "reflection": session.reflection,
                "focus_score": session.focus_score,
                "created_at": session.created_at,
            }
            for session in sessions[:5]
        ],
    }
    
    attempts = (
        db.query(models.ExamAttempt)
        .filter(models.ExamAttempt.user_name == current_user.user_name)
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
                "created_at": attempt.created_at
            }
            for attempt in attempts
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
        
    goal_data = {
        "id": goal.id,
        "subject": goal.subject,
        "title": goal.title,
        "target_score": goal.target_score,
        "exam_date": goal.exam_date,
        "days_left": days_left,
        "created_at": goal.created_at,
    }
    
    comment = ai_service.generate_goal_dashboard_comment(
        user_name=current_user.user_name,
        gpal=goal_data,
        checklist_summary=checklist_summary,
        session_summary=session_summary,
        attempt_summary=attempt_summary,
        weak_concepts=weak_concepts,
    )
    
    return {
        "success": True,
        "message": "목표별 대시보드가 생성되었습니다.",
        "goal": goal_data,
        "checklist_summary": checklist_summary,
        "session_summary": session_summary,
        "attempt_summary": attempt_summary,
        "weak_concepts": weak_concepts,
        "comment": comment,
    }