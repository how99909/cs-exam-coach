from app import models
from app.ai import grading_ai


def test_submit_exam_saves_attempt_answers_and_wrong_answer(
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
        question_text="BFS의 자료구조는?",
        answer="Queue",
        explanation="FIFO 구조를 사용한다.",
        concept="BFS",
        question_type="short_answer",
        difficulty="medium",
    )
    
    db.add(question)
    db.commit()
    db.refresh(question)
    
    monkeypatch.setattr(
        grading_ai,
        "grade_exam_answer",
        lambda **kwargs: {
            "is_correct": False,
            "feedback": "정답은 Queue입니다.",
        },
    )
    
    response = client.post(
        "/exam-attempts/submit",
        json={
            "subject": "algorithms",
            "title": "BFS Test",
            "answers": [
                {
                    "question_id": question.id,
                    "user_answer": "Stack",
                }
            ],
        },
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["total_questions"] == 1
    assert data["correct_count"] == 0
    assert data["score"] == 0
    
    attempt = db.get(
        models.ExamAttempt,
        data["attempt_id"],
    )
    
    assert attempt is not None
    assert attempt.user_id == user_a.id
    
    attempt_answers = (
        db.query(models.ExamAttemptAnswer)
        .filter(
            models.ExamAttemptAnswer.attempt_id == attempt.id
        )
        .all()
    )
    
    assert len(attempt_answers) == 1
    assert attempt_answers[0].is_correct is False
    
    wrong_answer = (
        db.query(models.WrongAnswer)
        .filter(models.WrongAnswer.question_id == question.id)
        .first()
    )
    
    assert wrong_answer is not None
    assert wrong_answer.user_id == user_a.id