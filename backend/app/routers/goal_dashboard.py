from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.analytics import dashboard_service
from app.services.exceptions import ResourceNotFoundError

router = APIRouter(prefix="/goal-dashboard", tags=["goal-dashboard"])


@router.post("")
def get_goal_dashboard(
    request: schemas.GoalDashboardRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = dashboard_service.get_goal_dashboard(
            db=db,
            user_id=current_user.id,
            user_name=current_user.user_name,
            goal_id=request.goal_id,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    
    return {
        "success": True,
        "message": "목표별 대시보드가 생성되었습니다.",
        **result,
    }
