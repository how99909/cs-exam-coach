from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import ai_service, models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/study-goals", tags=["study-goals"])


@router.post("")
def create_study_goal(
    request: schemas.StudyGoalCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if request.exam_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="exam_date는 오늘 이후 날짜여야 합니다.",
        )
        
    goal = models.StudyGoal(
        user_id=current_user.id,
        subject=request.subject,
        title=request.title,
        target_score=request.target_score,
        exam_date=request.exam_date,
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    return {
        "success": True,
        "message": "학습 목표가 생성되었습니다",
        "goal": {
            "id": goal.id,
            "subject": goal.subject,
            "title": goal.title,
            "target_score": goal.target_score,
            "exam_date": goal.exam_date,
            "created_at": goal.created_at,
        },
    }
    
    
@router.get("")
def list_study_goals(
    subject: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.StudyGoal).filter(
        models.StudyGoal.user_id == current_user.id
    )
    
    if subject:
        query = query.filter(models.StudyGoal.subject == subject)
        
    goals = query.order_by(models.StudyGoal.exam_date.asc()).all()
    
    return {
        "success": True,
        "goal_count": len(goals),
        "goals": [
            {
                "id": goal.id,
                "subject": goal.subject,
                "title": goal.title,
                "target_score": goal.target_score,
                "exam_date": goal.exam_date,
                "days_left": (goal.exam_date - date.today()).days,
                "created_at": goal.created_at,
            }
            for goal in goals
        ],
    }
    
    
@router.get("/{goal_id}/status")
def get_study_goal_status(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_study_goal_status(
        goal_id=goal_id,
        user_id=current_user.id,
        db=db,
    )


def _get_study_goal_status(
    goal_id: int,
    user_id: int,
    db: Session,
):
    goal = (
        db.query(models.StudyGoal)
        .filter(models.StudyGoal.id == goal_id)
        .filter(models.StudyGoal.user_id == user_id)
        .first()
    )
    
    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="학습 목표를 찾지 못했습니다.",
        )
        
    attempts = (
        db.query(models.ExamAttempt)
        .filter(models.ExamAttempt.user_id == user_id)
        .filter(models.ExamAttempt.subject == goal.subject)
        .order_by(models.ExamAttempt.created_at.desc())
        .limit(20)
        .all()
    )
    
    if attempts:
        current_average_score = round(
            sum(attempt.score for attempt in attempts) / len(attempts),
            2,
        )
        latest_score = attempts[0].score
    else:
        current_average_score = None
        latest_score = None
        
    if current_average_score is None:
        score_gap = None
    else:
        score_gap = goal.target_score - current_average_score
        
    weak_rows = (
        db.query(
            models.Question.concept,
            func.count(models.ExamAttemptAnswer.id).label("wrong_count"),
        )
        .join(
            models.ExamAttemptAnswer,
            models.ExamAttemptAnswer.question_id == models.Question.id,
        )
        .join(
            models.ExamAttempt,
            models.ExamAttempt.id == models.ExamAttemptAnswer.attempt_id,
        )
        .filter(models.ExamAttempt.user_name == user_id)
        .filter(models.ExamAttempt.subject == goal.subject)
        .filter(models.ExamAttemptAnswer.is_correct == False)
        .filter(models.Question.concept.isnot(None))
        .filter(models.Question.concept != "")
        .group_by(models.Question.concept)
        .order_by(func.count(models.ExamAttemptAnswer.id).desc())
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
    
    days_left = (goal.exam_date - date.today()).days
    
    return {
        "success": True,
        "goal": {
            "id": goal.id,
            "subject": goal.subject,
            "title": goal.title,
            "target_score": goal.target_score,
            "exam_date": goal.exam_date,
            "days_left": days_left,
        },
        "current_status": {
            "attempt_count": len(attempts),
            "current_average_score": current_average_score,
            "latest_score": latest_score,
            "target_score": goal.target_score,
            "score_gap": score_gap,
        },
        "weak_concepts": weak_concepts,
    }
    
    
@router.post("/strategy")
def generate_study_goal_strategy(
    request: schemas.StudyGoalStrategyRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    status_result = _get_study_goal_status(
        goal_id=request.goal_id,
        user_id=current_user.id,
        db=db,
    )
    
    goal = status_result["goal"]
    current_status = status_result["current_status"]
    weak_concepts = status_result["weak_concepts"]
    
    strategy = ai_service.generate_goal_strategy(
        user_name=current_user.user_name,
        goal=goal,
        current_status=current_status,
        weak_concepts=weak_concepts,
    )
    
    return {
        "success": True,
        "message": "목표 달성 전략이 생성되었습니다.",
        "goal": goal,
        "current_status": current_status,
        "weak_concepts": weak_concepts,
        "strategy": strategy,
    }
