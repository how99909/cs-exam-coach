from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models


def get_weak_concepts_from_attempts(
    db: Session,
    *,
    attempt_ids: list[int],
    limit: int = 10,
):
    if not attempt_ids:
        return []
    
    rows = (
        db.query(models.Question.concept, func.count(models.ExamAttemptAnswer.id).label("wrong_count"),)
        .join(models.ExamAttemptAnswer, models.ExamAttemptAnswer.question_id == models.Question.id,)
        .filter(models.ExamAttemptAnswer.attempt_id.in_(attempt_ids))
        .filter(models.ExamAttemptAnswer.is_correct == False)
        .filter(models.Question.concept.isnot(None))
        .filter(models.Question.concept != "")
        .group_by(models.Question.concept)
        .order_by(func.count(models.ExamAttemptAnswer.id).desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "concept": row.concept,
            "wrong_count": row.wrong_count,
        }
        for row in rows
    ]


def get_weak_concepts_from_wrong_answers(
    db: Session,
    *,
    user_id: int,
    subject: str | None = None,
    limit: int = 5,
):
    query = (
        db.query(
            models.WrongAnswer.concept,
            func.count(models.WrongAnswer.id).label("wrong_count"),
        )
        .filter(models.WrongAnswer.user_id == user_id)
        .filter(models.WrongAnswer.concept.isnot(None))
        .filter(models.WrongAnswer.concept != "")
    )

    if subject:
        query = (
            query.join(
                models.Question,
                models.WrongAnswer.question_id == models.Question.id,
            )
            .join(
                models.StudyMaterial,
                models.Question.material_id == models.StudyMaterial.id,
            )
            .filter(models.StudyMaterial.subject == subject)
        )

    rows = (
        query.group_by(models.WrongAnswer.concept)
        .order_by(func.count(models.WrongAnswer.id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "concept": row.concept,
            "wrong_count": row.wrong_count,
        }
        for row in rows
    ]
    
    
def build_checklist_summary(items):
    total_count = len(items)
    
    done_count = sum(1 for item in items if item.is_done)
    
    progress_rate = (
        round(done_count / total_count * 100, 2)
        if total_count else 0
    )
    
    return {
        "total_count": total_count,
        "done_count": done_count,
        "pending_count": total_count - done_count,
        "progress_rate": progress_rate,
    }
    
    
def build_session_summary(
    sessions,
):
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
    
    return{
        "session_count": len(sessions),
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 2),
        "avg_focus_score": avg_focus_score
    }
