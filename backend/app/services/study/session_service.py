from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError


def create_session(
    db: Session,
    *,
    user_id: int,
    subject: str,
    goal_id: int | None,
    checklist_item_id: int | None,
    duration_minutes: int,
    content: str,
    reflection: str | None,
    focus_score: int | None,
) -> models.StudySession:
    if duration_minutes <= 0:
        raise InvalidRequestError(
            "duration_minutes는 1 이상이어야 합니다."
        )
        
    if focus_score is not None and not 1<= focus_score <= 5:
        raise InvalidRequestError(
            "focus_score는 1점 이상 5점 이하이어야 합니다."
        )
        
    if goal_id is not None:
        goal = (
            db.query(models.StudyGoal)
            .filter(models.StudyGoal.id == goal_id)
            .filter(models.StudyGoal.user_id == user_id)
            .first()
        )
        
        if goal is None:
            raise ResourceNotFoundError(
                "연결할 학습 목표를 찾지 못했습니다."
            )

        if goal.subject != subject:
            raise InvalidRequestError(
                "학습 세션과 목표의 과목이 일치해야 합니다."
            )
            
    if checklist_item_id is not None:
        item = (
            db.query(models.StudyChecklistItem)
            .filter(models.StudyChecklistItem.id == checklist_item_id)
            .filter(models.StudyChecklistItem.user_id == user_id)
            .first()
        )
        
        if item is None:
            raise ResourceNotFoundError(
                "연결할 체크리스트 항목을 찾지 못했습니다."
            )

        if item.subject != subject:
            raise InvalidRequestError(
                "학습 세션과 체크리스트 항목의 과목이 일치해야 합니다."
            )

        if goal_id is not None and item.goal_id != goal_id:
            raise InvalidRequestError(
                "체크리스트 항목이 선택한 학습 목표에 속하지 않습니다."
            )
            
    session = models.StudySession(
        user_id=user_id,
        subject=subject,
        goal_id=goal_id,
        checklist_item_id=checklist_item_id,
        duration_minutes=duration_minutes,
        content=content,
        reflection=reflection,
        focus_score=focus_score,
    )
    
    try:
        db.add(session)
        db.commit()
        db.refresh(session)
    except Exception:
        db.rollback()
        raise
    
    return session
    
    
def list_sessions(
    db: Session,
    *,
    user_id: int,
    subject: str | None = None,
    goal_id: int | None = None,
    limit: int = 30,
) -> list[models.StudySession]:
    query = db.query(models.StudySession).filter(
        models.StudySession.user_id == user_id
    )
    
    if subject:
        query = query.filter(models.StudySession.subject == subject)
        
    if goal_id is not None:
        query = query.filter(models.StudySession.goal_id == goal_id)
        
    return (
        query
        .order_by(
            models.StudySession.created_at.desc()
        )
        .limit(limit)
        .all()
    )
    
    
def get_session_summary(
    db: Session,
    *,
    user_id: int,
    subject: str | None = None,
) -> dict:
    query = db.query(models.StudySession).filter(
        models.StudySession.user_id == user_id
    )
    
    if subject:
        query = query.filter(models.StudySession.subject == subject)
        
    sessions = query.all()
    
    total_minutes = sum(session.duration_minutes for session in sessions)
    
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
    
    subject_rows = (
        db.query(
            models.StudySession.subject,
            func.count(models.StudySession.id).label("session_count"),
            func.sum(models.StudySession.duration_minutes).label("total_minutes"),
            func.avg(models.StudySession.focus_score).label("avg_focus_score"),
        )
        .filter(models.StudySession.user_id == user_id)
    )

    if subject:
        subject_rows = subject_rows.filter(
            models.StudySession.subject == subject
        )

    subject_rows = (
        subject_rows
        .group_by(models.StudySession.subject)
        .all()
    )
    
    return {
        "session_count": len(sessions),
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 2),
        "avg_focus_score": avg_focus_score,
        "subject_summary": [
            {
                "subject": row.subject,
                "session_count": row.session_count,
                "total_minutes": int(row.total_minutes or 0),
                "total_hours": round(int(row.total_minutes or 0) / 60, 2),
                "avg_focus_score": round(float(row.avg_focus_score), 2)
                if row.avg_focus_score is not None
                else None,
            }
            for row in subject_rows
        ],
    }
