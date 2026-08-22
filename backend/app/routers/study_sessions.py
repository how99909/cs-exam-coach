from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/study-sessions", tags=["study-sessions"])


@router.post("")
def create_study_session(
    request: schemas.StudySessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user_name = current_user.user_name
    
    if request.duration_minutes <= 0:
        raise HTTPException(
            status_code=400,
            detail="duration_minutes는 1 이상이어야 합니다.",
        )
        
    if request.focus_score is not None and (
        request.focus_score < 1 or request.focus_score > 5
    ):
        raise HTTPException(
            status_code=400,
            detail="focus_score는 1점 이상 5점 이하이어야 합니다.",
        )
        
    if request.goal_id is not None:
        goal = (
            db.query(models.StudyGoal)
            .filter(models.StudyGoal.id == request.goal_id)
            .filter(models.StudyGoal.user_id == current_user.id)
            .first()
        )
        
        if goal is None:
            raise HTTPException(
                status_code=404,
                detail="연결할 학습 목표를 찾지 못했습니다.",
            )
            
    if request.checklist_item_id is not None:
        checklist_item = (
            db.query(models.StudyChecklistItem)
            .filter(models.StudyChecklistItem.id == request.checklist_item_id)
            .filter(models.StudyChecklistItem.user_id == current_user.id)
            .first()
        )
        
        if checklist_item is None:
            raise HTTPException(
                status_code=404,
                detail="연결할 체크리스트 항목을 찾지 못했습니다.",
            )
            
    session = models.StudySession(
        user_id=current_user.id,
        subject=request.subject,
        goal_id=request.goal_id,
        checklist_item_id=request.checklist_item_id,
        duration_minutes=request.duration_minutes,
        content=request.content,
        reflection=request.reflection,
        focus_score=request.focus_score,
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "success": True,
        "message": "학습 세션이 기록되었습니다.",
        "session": {
            "id": session.id,
            "user_name": session.user_name,
            "subject": session.subject,
            "goal_id": session.goal_id,
            "checklist_item_id": session.checklist_item_id,
            "duration_minutes": session.duration_minutes,
            "content": session.content,
            "reflection": session.reflection,
            "focus_score": session.focus_score,
            "created_at": session.created_at,
        },
    }
    
    
@router.get("")
def list_study_sessions(
    subject: str | None = None,
    goal_id: int | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.StudySession).filter(
        models.StudySession.user_id == current_user.id
    )
    
    if subject:
        query = query.filter(models.StudySession.subject == subject)
        
    if goal_id is not None:
        query = query.filter(models.StudySession.goal_id == goal_id)
        
    sessions = (
        query.order_by(models.StudySession.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return {
        "success": True,
        "session_count": len(sessions),
        "sessions": [
            {
                "id": session.id,
                "subject": session.subject,
                "goal_id": session.goal_id,
                "checklist_item_id": session.checklist_item_id,
                "duration_minutes": session.duration_minutes,
                "content": session.content,
                "reflection": session.reflection,
                "focus_score": session.focus_score,
                "created_at": session.created_at,
            }
            for session in sessions
        ],
    }
    
    
@router.get("/summary")
def get_study_session_summary(
    subject: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.StudySession).filter(
        models.StudySession.user_id == current_user.id
    )
    
    if subject:
        query = query.filter(models.StudySession.subject == subject)
        
    sessions = query.all()
    
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
    
    subject_rows = (
        db.query(
            models.StudySession.subject,
            func.count(models.StudySession.id).label("session_count"),
            func.sum(models.StudySession.duration_minutes).label("total_minutes"),
            func.avg(models.StudySession.focus_score).label("avg_focus_score"),
        )
        .filter(models.StudySession.user_id == current_user.id)
        .group_by(models.StudySession.subject)
        .all()
    )
    
    subject_summary = [
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
    ]
    
    return {
        "success": True,
        "session_count": len(sessions),
        "total_minutes": total_minutes,
        "total_hours": total_hours,
        "avg_focus_score": avg_focus_score,
        "subject_summary": subject_summary,
    }
