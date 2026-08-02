from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])


def validate_score(score: int, field_name: str):
    if score < 1 or score > 5:
        return {
            "success": False,
            "message": f"{field_name} 점수는 1에서 5 사이여야 합니다.",
        }
    return None


@router.post("/question")
def create_question_feedback(
    request: schemas.QuestionFeedbackCreate, 
    db: Session = Depends(get_db)
):
    validations = [
        validate_score(request.quality_score, "quality_score"),
        validate_score(request.explanation_score, "explanation_score"),
        validate_score(request.exam_relevance_score, "exam_relevance_score"),
        validate_score(request.difficulty_match_score, "difficulty_match_score"),
    ]
    
    for validation in validations:
        if validation is not None:
            return validation
        
    feedback = models.QuestionFeedback(
        user_name=request.user_name,
        question_id=request.question_id,
        quality_score=request.quality_score,
        explanation_score=request.explanation_score,
        exam_relevance_score=request.exam_relevance_score,
        difficulty_match_score=request.difficulty_match_score,
        comment=request.comment,
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return {
        "success": True,
        "message": "문제 평가가 저장되었습니다.",
        "feedback_id": feedback.id,
    }
    
    
@router.get("/question/{question_id}")
def get_question_feedback_summary(
    question_id: int, 
    db: Session = Depends(get_db)
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
        .first()
    )
    
    comments = (
        db.query(models.QuestionFeedback.comment)
        .filter(models.QuestionFeedback.question_id == question_id)
        .filter(models.QuestionFeedback.comment.isnot(None))
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
    
    
@router.get("/summary")
def get_feedback_summary(
    user_name: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        func.count(models.QuestionFeedback.id).label("feedback_count"),            
        func.avg(models.QuestionFeedback.quality_score).label("avg_quality_score"),
        func.avg(models.QuestionFeedback.explanation_score).label("avg_explanation_score"),
        func.avg(models.QuestionFeedback.exam_relevance_score).label("avg_exam_relevance_score"),
        func.avg(models.QuestionFeedback.difficulty_match_score).label("avg_difficulty_match_score"),
    )
    
    if user_name:
        query = query.filter(models.QuestionFeedback.user_name == user_name)
    
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