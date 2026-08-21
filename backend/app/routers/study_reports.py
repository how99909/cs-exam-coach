from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import ai_service, models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/study-reports", tags=["study-reports"])


@router.post("/generate")
def generate_personal_study_report(
    request: schemas.StudyReportRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    attempt_query = db.query(models.ExamAttempt).filter(
        models.ExamAttempt.user_name == current_user.user_name
    )
    
    if request.subject:
        attempt_query = attempt_query.filter(models.ExamAttempt.subject == request.subject)
        
    attempts = (
        attempt_query.order_by(models.ExamAttempt.created_at.desc())
        .limit(request.limit)
        .all()
    )
    
    if not attempts:
        raise HTTPException(
            status_code=404,
            detail="학습 리포트를 생성할 응시 기록이 없습니다.",
        )
        
    attempt_ids = [attempt.id for attempt in attempts]
    
    average_score = round(
        sum(attempt.score for attempt in attempts) / len(attempts),
        2,
    )
    
    latest_score = attempts[0].score
    best_score = max(attempt.score for attempt in attempts)
    lowest_score = min(attempt.score for attempt in attempts)
    
    attempt_summary = {
        "attempt_count": len(attempts),
        "average_score": average_score,
        "latest_score": latest_score,
        "best_score": best_score,
        "lowest_score": lowest_score,
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
    
    report = ai_service.generate_study_report(
        user_name=current_user.user_name,
        subject=request.subject,
        attempt_summary=attempt_summary,
        weak_concepts=weak_concepts,
        score_trend=score_trend,
    )
    
    return {
        "success": True,
        "message": "개인 맞춤 학습 리포트가 생성되었습니다.",
        "attempt_summary": attempt_summary,
        "weak_concepts": weak_concepts,
        "score_trend": score_trend,
        "report": report,
    }