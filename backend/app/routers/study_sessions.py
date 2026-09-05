from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.study import session_service
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError


router = APIRouter(prefix="/study-sessions", tags=["study-sessions"])


@router.post("")
def create_study_session(
    request: schemas.StudySessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = session_service.create_session(
            db=db,
            user_id=current_user.id,
            subject=request.subject,
            goal_id=request.goal_id,
            checklist_item_id=request.checklist_item_id,
            duration_minutes=request.duration_minutes,
            content=request.content,
            reflection=request.reflection,
            focus_score=request.focus_score
        )
        
    except InvalidRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc
        
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc
    
    return {
        "success": True,
        "message": "학습 세션이 기록되었습니다.",
        "session": _serialize_session(result),
    }
    
    
@router.get("")
def list_study_sessions(
    subject: str | None = None,
    goal_id: int | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    sessions = session_service.list_sessions(
        db=db,
        user_id=current_user.id,
        subject=subject,
        goal_id=goal_id,
        limit=limit
    )
    
    return {
        "success": True,
        "session_count": len(sessions),
        "sessions": [
            _serialize_session(session)
            for session in sessions
        ],
    }
    
    
@router.get("/summary")
def get_study_session_summary(
    subject: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = session_service.get_session_summary(
        db=db,
        user_id=current_user.id,
        subject=subject,
    )
    
    return {
        "success": True,
        **result,
    }


def _serialize_session(
    session: models.StudySession,
) -> dict:
    result = {
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

    return result
