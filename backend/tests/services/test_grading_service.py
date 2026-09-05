from app import models
from app.ai import grading_ai
from app.services import grading_service


def test_grading_service_saves_result(
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
        question_text="BFS란?",
        answer="너비 우선 탐색",
        explanation="",
        concept="BFS",
        question_type="short_answer",
        difficulty="medium",
    )
    
    db.add(question)
    db.commit()
    
    monkeypatch.setattr(
        grading_ai,
        "grade_answer",
        lambda **kwargs: {
            "is_correct": False,
            "feedback": "복습 필요",
            "concept": "BFS",
        },
    )
    
    result = grading_service.grade_answer(
        db=db,
        user_id=user_a.id,
        question_id=question.id,
        user_answer="DFS",
    )
    
    assert result["is_correct"] is False
    
    wrong_answer = (
        db.query(models.WrongAnswer)
        .filter(models.WrongAnswer.question_id == question.id)
        .first()
    )
    
    assert wrong_answer is not None