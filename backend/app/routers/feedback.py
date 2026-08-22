from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user

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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    question = (
        db.query(models.Question)
        .join(
            models.StudyMaterial,
            models.Question.material_id == models.StudyMaterial.id,
        )
        .filter(models.Question.id == request.question_id)
        .filter(models.StudyMaterial.user_id == current_user.id)
        .first()
    )
    if question is None:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

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
        user_id=current_user.id,
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
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
        .filter(models.QuestionFeedback.user_id == current_user.id)
        .first()
    )
    
    comments = (
        db.query(models.QuestionFeedback.comment)
        .filter(models.QuestionFeedback.question_id == question_id)
        .filter(models.QuestionFeedback.user_id == current_user.id)
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(
        func.count(models.QuestionFeedback.id).label("feedback_count"),            
        func.avg(models.QuestionFeedback.quality_score).label("avg_quality_score"),
        func.avg(models.QuestionFeedback.explanation_score).label("avg_explanation_score"),
        func.avg(models.QuestionFeedback.exam_relevance_score).label("avg_exam_relevance_score"),
        func.avg(models.QuestionFeedback.difficulty_match_score).label("avg_difficulty_match_score"),
    )
    
    if current_user.id:
        query = query.filter(models.QuestionFeedback.user_id == current_user.id)
    
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
    
    
@router.get("/low-score-questions")
def get_low_score_questions(
    threshold: float = 3.0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    results = (
        db.query(
            models.QuestionFeedback.question_id,
            func.count(models.QuestionFeedback.id).label("feedback_count"),
            func.avg(models.QuestionFeedback.quality_score).label("avg_quality_score"),
            func.avg(models.QuestionFeedback.explanation_score).label("avg_explanation_score"),
            func.avg(models.QuestionFeedback.exam_relevance_score).label("avg_exam_relevance_score"),
            func.avg(models.QuestionFeedback.difficulty_match_score).label("avg_difficulty_match_score"),
        )
        .filter(models.QuestionFeedback.user_id == current_user.id)
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
    
    
@router.get("/low-exam-relevance")
def get_low_exam_relevance_questions(
    threshold: float = 3.0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    results = (
        db.query(
            models.QuestionFeedback.question_id,
            func.count(models.QuestionFeedback.id).label("feedback_count"),
            func.avg(models.QuestionFeedback.quality_score).label("avg_quality_score"),
            func.avg(models.QuestionFeedback.explanation_score).label("avg_explanation_score"),
            func.avg(models.QuestionFeedback.exam_relevance_score).label("avg_exam_relevance_score"),
            func.avg(models.QuestionFeedback.difficulty_match_score).label("avg_difficulty_match_score"),
        )
        .filter(models.QuestionFeedback.user_id == current_user.id)
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
    
    
@router.get("/recent-comments")
def get_recent_feedback_comments(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    comments = (
        db.query(models.QuestionFeedback)
        .filter(models.QuestionFeedback.user_id == current_user.id)
        .filter(models.QuestionFeedback.comment.isnot(None))
        .filter(models.QuestionFeedback.comment != "")
        .order_by(models.QuestionFeedback.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": feedback.id,
            "user_name": feedback.user_name,
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
    
    
@router.get("/admin-dashboard")
def get_admin_feedback_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    summary_result = (
        db.query(
            func.count(models.QuestionFeedback.id).label("feedback_count"),
            func.avg(models.QuestionFeedback.quality_score).label("avg_quality_score"),
            func.avg(models.QuestionFeedback.explanation_score).label("avg_explanation_score"),
            func.avg(models.QuestionFeedback.exam_relevance_score).label("avg_exam_relevance_score"),
            func.avg(models.QuestionFeedback.difficulty_match_score).label("avg_difficulty_match_score")
        )
        .filter(models.QuestionFeedback.user_id == current_user.id)
        .first()
    )
    
    if summary_result.feedback_count == 0:
        return {
            "feedback_count": 0,
            "message": "아직 평가 데이터가 없습니다.",
            "summary": None,
            "low_score_questions": [],
            "low_exam_relevance_questions": [],
            "recent_comments": [],
        }
        
    low_score_questions = get_low_score_questions(db=db, current_user=current_user)
    low_exam_relevance_questions = get_low_exam_relevance_questions(
        db=db,
        current_user=current_user,
    )
    recent_comments = get_recent_feedback_comments(
        db=db,
        current_user=current_user,
    )
    
    return {
        "feedback_count": summary_result.feedback_count,
        "summary": {
            "avg_quality_score": round(float(summary_result.avg_quality_score), 2),
            "avg_explanation_score": round(float(summary_result.avg_explanation_score), 2),
            "avg_exam_relevance_score": round(float(summary_result.avg_exam_relevance_score), 2),
            "avg_difficulty_match_score": round(float(summary_result.avg_difficulty_match_score), 2),
        },
        "low_score_questions": low_score_questions,
        "low_exam_relevance_questions": low_exam_relevance_questions,
        "recent_comments": recent_comments,
    }
