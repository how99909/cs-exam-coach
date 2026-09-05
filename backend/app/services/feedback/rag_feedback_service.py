from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError


def validate_score(score: int, field_name: str) -> None:
    if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
        raise InvalidRequestError(
            f"{field_name} 점수는 1에서 5 사이여야 합니다."
        )
        
        
def create_rag_feedback(
    db: Session,
    *,
    user_id: int,
    subject: str,
    material_id: int | None,
    question: str,
    answer: str,
    accuracy_score: int,
    grounding_score: int,
    source_relevance_score: int,
    helpfulness_score: int,
    comment: str | None,
) -> models.RagAnswerFeedback:
    feedback = models.RagAnswerFeedback(
        user_id=user_id,
        subject=subject,
        material_id=material_id,
        question=question,
        answer=answer,
        accuracy_score=accuracy_score,
        grounding_score=grounding_score,
        source_relevance_score=source_relevance_score,
        helpfulness_score=helpfulness_score,
        comment=comment,
    )
    
    try:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
    except Exception:
        db.rollback()
        raise
    
    return feedback


def get_rag_feedback_summary(
    db: Session,
    *,
    user_id: int,
    subject: str | None = None,
):
    query = db.query(
        func.count(models.RagAnswerFeedback.id).label("feedback_count"),            
        func.avg(models.RagAnswerFeedback.accuracy_score).label("avg_accuracy_score"),
        func.avg(models.RagAnswerFeedback.grounding_score).label("avg_grounding_score"),
        func.avg(models.RagAnswerFeedback.source_relevance_score).label(
            "avg_source_relevance_score"
        ),
        func.avg(models.RagAnswerFeedback.helpfulness_score).label(
            "avg_helpfulness_score"
        ),
    )
    
    query = query.filter(models.RagAnswerFeedback.user_id == user_id)
        
    if subject:
        query = query.filter(models.RagAnswerFeedback.subject == subject)
    
    return query.first()


def get_recent_rag_feedback(
    db: Session,
    *,
    user_id: int,
    subject: str | None = None,
    limit: int = 20,
):
    query = db.query(models.RagAnswerFeedback)
        
    query = query.filter(models.RagAnswerFeedback.user_id == user_id)
        
    if subject:
        query = query.filter(models.RagAnswerFeedback.subject == subject)
        
    return (
        query.order_by(models.RagAnswerFeedback.created_at.desc())
        .limit(limit)
        .all()
    )


def create_feedback(
    db: Session,
    *,
    user_id: int,
    subject: str,
    material_id: int | None,
    question: str,
    answer: str,
    accuracy_score: int,
    grounding_score: int,
    source_relevance_score: int,
    helpfulness_score: int,
    comment: str | None,
):
    subject = subject.strip()
    question = question.strip()
    answer = answer.strip()

    if not subject:
        raise InvalidRequestError("과목을 입력해야 합니다.")
    if not question:
        raise InvalidRequestError("평가할 질문을 입력해야 합니다.")
    if not answer:
        raise InvalidRequestError("평가할 답변을 입력해야 합니다.")

    if material_id is not None:
        material = (
            db.query(models.StudyMaterial)
            .filter(models.StudyMaterial.id == material_id)
            .filter(models.StudyMaterial.user_id == user_id)
            .first()
        )
        if material is None:
            raise ResourceNotFoundError(
                "학습 자료를 찾을 수 없습니다."
            )

        if material.subject != subject:
            raise InvalidRequestError(
                "학습 자료의 과목과 평가 과목이 일치하지 않습니다."
            )

    validate_score(accuracy_score, "accuracy_score")
    validate_score(grounding_score, "grounding_score")
    validate_score(source_relevance_score, "source_relevance_score")
    validate_score(helpfulness_score, "helpfulness_score")

    if comment is not None:
        comment = comment.strip() or None

    feedback = create_rag_feedback(
        db=db,
        user_id=user_id,
        subject=subject,
        material_id=material_id,
        question=question,
        answer=answer,
        accuracy_score=accuracy_score,
        grounding_score=grounding_score,
        source_relevance_score=source_relevance_score,
        helpfulness_score=helpfulness_score,
        comment=comment,
    )
    
    return {
        "feedback_id": feedback.id,
    }
    

def get_summary(
    db: Session,
    *,
    user_id: int,
    subject: str | None,
):
    subject = _normalize_optional_subject(subject)
    result = get_rag_feedback_summary(
        db=db,
        user_id=user_id,
        subject=subject,
    )
    
    if result.feedback_count == 0:
        return {
            "feedback_count": 0,
            "message": "아직 RAG 답변 평가 데이터가 없습니다.",
        }
        
    return {
        "feedback_count": result.feedback_count,
        "avg_accuracy_score": round(float(result.avg_accuracy_score), 2),
        "avg_grounding_score": round(float(result.avg_grounding_score), 2),
        "avg_source_relevance_score": round(
            float(result.avg_source_relevance_score),
            2
        ),
        "avg_helpfulness_score": round(float(result.avg_helpfulness_score), 2),
    }
    

def get_recent(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    subject: str | None,
    limit: int,
):
    if not 1 <= limit <= 100:
        raise InvalidRequestError("limit은 1 이상 100 이하이어야 합니다.")

    subject = _normalize_optional_subject(subject)
    feedback_items = get_recent_rag_feedback(
        db=db,
        user_id=user_id,
        subject=subject,
        limit=limit,
    )
    
    return [
        {
            "id": item.id,
            "user_name": user_name,
            "subject": item.subject,
            "material_id": item.material_id,
            "question": item.question,
            "accuracy_score": item.accuracy_score,
            "grounding_score": item.grounding_score,
            "source_relevance_score": item.source_relevance_score,
            "helpfulness_score": item.helpfulness_score,
            "comment": item.comment,
            "created_at": item.created_at,
        }
        for item in feedback_items
    ]


def _normalize_optional_subject(subject: str | None) -> str | None:
    if subject is None:
        return None
    return subject.strip() or None
