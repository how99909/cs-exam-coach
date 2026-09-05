import pytest

from app import models
from app.ai import grading_ai
from app.services import exam_attempt_service
from app.services.exceptions import ResourceNotFoundError


def test_submit_exam_attempt_saves_attempt(
    db,
    user_a,
    monkeypatch,
):
    material = models.StudyMaterial(
        user_id=user_a.id,
        subject="algorithms",
        content="BFS",
    )
    
    db.add(material)
    db.flush()
    
    question = models.Question(
        material_id=material.id,
        question_text="BFS 자료구조?",
        answer="Queue",
        explanation="FIFO",
        concept="BFS",
        question_type="short_answer",
        difficulty="medium",
    )
    
    db.add(question)
    db.commit()
    
    monkeypatch.setattr(
        grading_ai,
        "grade_exam_answer",
        lambda **kwargs: {
            "is_correct": False,
            "feedback": "Queue가 정답입니다.",
        },
    )
    
    attempt, results = (
        exam_attempt_service.submit_exam_attempt(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            title="Test",
            answers=[
                (
                    question.id,
                    "Stack",
                )
            ],
        )
    )
    
    assert attempt.id is not None
    assert attempt.user_id == user_a.id
    assert attempt.score == 0
    assert len(results) == 1
    
    assert (
        db.query(models.ExamAttemptAnswer)
        .count() == 1
    )
    
    assert (
        db.query(models.WrongAnswer)
        .count() == 1
    )
    
    
def test_submit_rejects_other_users_question(
    db,
    user_a,
    user_b,
):
    material = models.StudyMaterial(
        user_id=user_b.id,
        subject="algorithms",
        content="BFS",
    )
    
    db.add(material)
    db.flush()
    
    question = models.Question(
        material_id=material.id,
        question_text="BFS?",
        answer="Queue",
        explanation="",
        concept="BFS",
        question_type="short_answer",
        difficulty="medium",
    )
    
    db.add(question)
    db.commit()
    
    with pytest.raises(
        ResourceNotFoundError
    ):
        exam_attempt_service.submit_exam_attempt(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            title="Test",
            answers=[
                (
                    question.id,
                    "Queue",
                )
            ],
        )
        
        
def test_empty_analytics(
    db,
    user_a
):
    result = (
        exam_attempt_service.get_exam_attempt_analytics(
            db=db,
            user_id=user_a.id,
        )
    )
    
    assert result["attempt_count"] == 0
    assert result["average_score"] is None
    assert result["score_trend"] == []