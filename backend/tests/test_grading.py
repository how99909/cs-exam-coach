from app import models
from app.ai import grading_ai


def test_grade_answer_saves_wrong_answer(
    client,
    db,
    user_a,
    auth_as,
    monkeypatch,
):
    auth_as(user_a)
    
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
        explanation="레벨 순서 탐색",
        concept="BFS",
        question_type="short_answer",
        difficulty="medium",
    )
    
    db.add(question)
    db.commit()
    db.refresh(question)
    
    monkeypatch.setattr(
        grading_ai,
        "grade_answer",
        lambda **kwargs: {
            "is_correct": False,
            "feedback": "큐를 이용한다는 설명이 필요합니다.",
            "concept": "BFS",
        },
    )
    
    response = client.post(
        "/grading/grade",
        json={
            "question_id": question.id,
            "user_answer": "그래프 탐색",
        },
    )
    
    assert response.status_code == 200
    assert response.json()["is_correct"] is False
    
    wrong_answer = (
        db.query(models.WrongAnswer)
        .filter(
            models.WrongAnswer.question_id == question.id
        )
        .first()
    )
    
    assert wrong_answer is not None
    assert wrong_answer.user_id == user_a.id
    assert wrong_answer.concept == "BFS"
    assert wrong_answer.is_correct is False