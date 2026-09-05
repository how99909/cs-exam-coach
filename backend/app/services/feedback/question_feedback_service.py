from math import isfinite

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError


def validate_score(score: int, field_name: str) -> None:
    if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
        raise InvalidRequestError(
            f"{field_name} 점수는 1에서 5 사이여야 합니다."
        )


def create_feedback(
    db: Session,
    *,
    user_id: int,
    question_id: int,
    quality_score: int,
    explanation_score: int,
    exam_relevance_score: int,
    difficulty_match_score: int,
    comment: str | None,
):
    question = (
        db.query(models.Question)
        .join(
            models.StudyMaterial,
            models.Question.material_id == models.StudyMaterial.id,
        )
        .filter(models.Question.id == question_id)
        .filter(models.StudyMaterial.user_id == user_id)
        .first()
    )
    if question is None:
        raise ResourceNotFoundError(
            "문제를 찾을 수 없습니다."
        )

    validate_score(quality_score, "quality_score")
    validate_score(explanation_score, "explanation_score")
    validate_score(exam_relevance_score, "exam_relevance_score")
    validate_score(difficulty_match_score, "difficulty_match_score")

    if comment is not None:
        comment = comment.strip() or None
        
    feedback = models.QuestionFeedback(
        user_id=user_id,
        question_id=question_id,
        quality_score=quality_score,
        explanation_score=explanation_score,
        exam_relevance_score=exam_relevance_score,
        difficulty_match_score=difficulty_match_score,
        comment=comment,
    )
    
    try:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
    except Exception:
        db.rollback()
        raise
    
    return {
        "feedback_id": feedback.id,
    }
    

def get_question_summary(
    db: Session,
    *,
    user_id: int,
    question_id: int, 
):
    result = (
        db.query(
            func.count(models.QuestionFeedback.id).label("feedback_count"),
            func.avg(models.QuestionFeedback.quality_score).label("avg_quality_score"),
            func.avg(models.QuestionFeedback.explanation_score).label("avg_explanation_score"),
            func.avg(models.QuestionFeedback.exam_relevance_score).label("avg_exam_relevance_score"),
            func.avg(models.QuestionFeedback.difficulty_match_score).label("avg_difficulty_match_score"),
        )
        .filter(models.QuestionFeedback.question_id == question_id)
        .filter(models.QuestionFeedback.user_id == user_id)
        .first()
    )
    
    comments = (
        db.query(models.QuestionFeedback.comment)
        .filter(models.QuestionFeedback.question_id == question_id)
        .filter(models.QuestionFeedback.user_id == user_id)
        .filter(models.QuestionFeedback.comment.isnot(None))
        .filter(models.QuestionFeedback.comment != "")
        .order_by(models.QuestionFeedback.created_at.desc())
        .limit(5)
        .all()
    )
    
    if result.feedback_count == 0:
        return {
            "question_id": question_id,
            "feedback_count": 0,
            "message": "아직 평가가 없습니다.",
        }
        
    return {
        "question_id": question_id,
        "feedback_count": result.feedback_count,
        "avg_quality_score": round(float(result.avg_quality_score), 2),
        "avg_explanation_score": round(float(result.avg_explanation_score), 2),
        "avg_exam_relevance_score": round(float(result.avg_exam_relevance_score), 2),
        "avg_difficulty_match_score": round(float(result.avg_difficulty_match_score), 2),
        "recent_comments": [comment[0] for comment in comments if comment[0]],
    }
    

def get_summary(
    db: Session,
    *,
    user_id: int,
):
    query = db.query(
        func.count(models.QuestionFeedback.id).label("feedback_count"),            
        func.avg(models.QuestionFeedback.quality_score).label("avg_quality_score"),
        func.avg(models.QuestionFeedback.explanation_score).label("avg_explanation_score"),
        func.avg(models.QuestionFeedback.exam_relevance_score).label("avg_exam_relevance_score"),
        func.avg(models.QuestionFeedback.difficulty_match_score).label("avg_difficulty_match_score"),
    )
    
    query = query.filter(models.QuestionFeedback.user_id == user_id)
    
    result = query.first()
        
    if result.feedback_count == 0:
        return {
            "feedback_count": 0,
            "message": "아직 평가가 없습니다.",
        }

    return {
        "feedback_count": result.feedback_count,
        "avg_quality_score": round(float(result.avg_quality_score), 2),
        "avg_explanation_score": round(float(result.avg_explanation_score), 2),
        "avg_exam_relevance_score": round(float(result.avg_exam_relevance_score), 2),
        "avg_difficulty_match_score": round(float(result.avg_difficulty_match_score), 2),
    }
    

def get_low_score_questions(
    db: Session,
    *,
    user_id: int,
    threshold: float,
):
    _validate_threshold(threshold)

    results = (
        db.query(
            models.QuestionFeedback.question_id,
            func.count(models.QuestionFeedback.id).label("feedback_count"),
            func.avg(models.QuestionFeedback.quality_score).label("avg_quality_score"),
            func.avg(models.QuestionFeedback.explanation_score).label("avg_explanation_score"),
            func.avg(models.QuestionFeedback.exam_relevance_score).label("avg_exam_relevance_score"),
            func.avg(models.QuestionFeedback.difficulty_match_score).label("avg_difficulty_match_score"),
        )
        .filter(models.QuestionFeedback.user_id == user_id)
        .group_by(models.QuestionFeedback.question_id)
        .having(func.avg(models.QuestionFeedback.quality_score) <= threshold)
        .order_by(func.avg(models.QuestionFeedback.quality_score).asc())
        .limit(20)
        .all()
    )
    
    return [
        {
            "question_id": result.question_id,
            "avg_quality_score": round(float(result.avg_quality_score), 2),
            "avg_explanation_score": round(float(result.avg_explanation_score), 2),
            "avg_exam_relevance_score": round(float(result.avg_exam_relevance_score), 2),
            "avg_difficulty_match_score": round(float(result.avg_difficulty_match_score), 2),
            "feedback_count": result.feedback_count,
        }
        for result in results
    ]
    

def get_low_exam_relevance_questions(
    db: Session,
    *,
    user_id: int,
    threshold: float,
    
):
    _validate_threshold(threshold)

    results = (
        db.query(
            models.QuestionFeedback.question_id,
            func.count(models.QuestionFeedback.id).label("feedback_count"),
            func.avg(models.QuestionFeedback.quality_score).label("avg_quality_score"),
            func.avg(models.QuestionFeedback.explanation_score).label("avg_explanation_score"),
            func.avg(models.QuestionFeedback.exam_relevance_score).label("avg_exam_relevance_score"),
            func.avg(models.QuestionFeedback.difficulty_match_score).label("avg_difficulty_match_score"),
        )
        .filter(models.QuestionFeedback.user_id == user_id)
        .group_by(models.QuestionFeedback.question_id)
        .having(func.avg(models.QuestionFeedback.exam_relevance_score) <= threshold)
        .order_by(func.avg(models.QuestionFeedback.exam_relevance_score).asc())
        .limit(20)
        .all()
    )
    
    return [
        {
            "question_id": result.question_id,
            "avg_quality_score": round(float(result.avg_quality_score), 2),
            "avg_explanation_score": round(float(result.avg_explanation_score), 2),
            "avg_exam_relevance_score": round(float(result.avg_exam_relevance_score), 2),
            "avg_difficulty_match_score": round(float(result.avg_difficulty_match_score), 2),
            "feedback_count": result.feedback_count,
        }
        for result in results
    ]
    

def get_recent_comments(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    limit: int,
):
    if not 1 <= limit <= 100:
        raise InvalidRequestError("limit은 1 이상 100 이하이어야 합니다.")

    comments = (
        db.query(models.QuestionFeedback)
        .filter(models.QuestionFeedback.user_id == user_id)
        .filter(models.QuestionFeedback.comment.isnot(None))
        .filter(models.QuestionFeedback.comment != "")
        .order_by(models.QuestionFeedback.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": feedback.id,
            "user_name": user_name,
            "question_id": feedback.question_id,
            "quality_score": feedback.quality_score,
            "explanation_score": feedback.explanation_score,
            "exam_relevance_score": feedback.exam_relevance_score,
            "difficulty_match_score": feedback.difficulty_match_score,
            "comment": feedback.comment,
            "created_at": feedback.created_at,
        }
        for feedback in comments
    ]
    

def get_admin_dashboard(
    db: Session,
    *,
    user_id: int,
    user_name: str,
):
    summary = get_summary(
        db,
        user_id=user_id
    )
    
    if summary["feedback_count"] == 0:
        return {
            "feedback_count": 0,
            "message": "아직 평가 데이터가 없습니다.",
            "summary": None,
            "low_score_questions": [],
            "low_exam_relevance_questions": [],
            "recent_comments": [],
        }
    
    return {
        "feedback_count": summary["feedback_count"],
        "summary": {
            key: value
            for key,  value in summary.items()
            if key != "feedback_count"
        },
        "low_score_questions": get_low_score_questions(
            db,
            user_id=user_id,
            threshold=3.0,
        ),
        "low_exam_relevance_questions": get_low_exam_relevance_questions(
            db,
            user_id=user_id,
            threshold=3.0,
        ),
        "recent_comments": get_recent_comments(
            db,
            user_id=user_id,
            user_name=user_name,
            limit=10,
        ),
    }


def _validate_threshold(threshold: float) -> None:
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not isfinite(float(threshold))
        or not 1 <= threshold <= 5
    ):
        raise InvalidRequestError("threshold는 1 이상 5 이하이어야 합니다.")
