from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.ai import study_ai
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError


def create_goal(
    db: Session,
    *,
    user_id: int,
    subject: str,
    title: str,
    target_score: int,
    exam_date: date,
) -> models.StudyGoal:
    if exam_date < date.today():
        raise InvalidRequestError(
            "exam_date는 오늘 이후 날짜여야 합니다."
        )
        
    goal = models.StudyGoal(
        user_id=user_id,
        subject=subject,
        title=title,
        target_score=target_score,
        exam_date=exam_date,
    )
    
    try:
        db.add(goal)
        db.commit()
        db.refresh(goal)
    except Exception:
        db.rollback()
        raise
    
    return goal
    
    
def list_goals(
    db: Session,
    *,
    user_id: int,
    subject: str | None = None,
) -> list[models.StudyGoal]:
    query = db.query(models.StudyGoal).filter(
        models.StudyGoal.user_id == user_id
    )
    
    if subject:
        query = query.filter(models.StudyGoal.subject == subject)
        
    return (
        query
        .order_by(models.StudyGoal.exam_date.asc())
        .all()
    )
    
    
def get_goal_status(
    db: Session,
    *,
    user_id: int,
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
        
    score_gap = (
        goal.target_score - current_average_score
        if current_average_score is not None
        else None
    )
        
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
        .filter(models.ExamAttempt.user_id == user_id)
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
    
    return {
        "goal": {
            "id": goal.id,
            "subject": goal.subject,
            "title": goal.title,
            "target_score": goal.target_score,
            "exam_date": goal.exam_date,
            "days_left": (goal.exam_date - date.today()).days,
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
    
    
def generate_goal_strategy(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    goal_id: int,
) -> dict[str, Any]:
    status = get_goal_status(
        goal_id=goal_id,
        user_id=user_id,
        db=db,
    )
    
    strategy = study_ai.generate_goal_strategy(
        user_name=user_name,
        goal=status["goal"],
        current_status=status["current_status"],
        weak_concepts=status["weak_concepts"],
    )
    
    return {
        **status,
        "strategy": strategy,
    }
