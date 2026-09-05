from datetime import timedelta

from app import models
from app.time_utils import utc_now


def _create_question(db, user, *, subject="algorithms", created_at=None):
    material = models.StudyMaterial(
        user_id=user.id,
        subject=subject,
        content="Study material",
    )
    db.add(material)
    db.flush()
    question = models.Question(
        material_id=material.id,
        question_text=f"Question for {subject}",
        answer="Answer",
        explanation="Explanation",
        concept="Concept",
        question_type="short_answer",
        difficulty="medium",
        created_at=created_at or utc_now(),
    )
    db.add(question)
    db.flush()
    return question


def test_question_history_is_flat_ordered_limited_and_user_scoped(
    auth_client,
    db,
    user_a,
    user_b,
):
    now = utc_now()
    older = _create_question(db, user_a, created_at=now - timedelta(minutes=2))
    newer = _create_question(db, user_a, created_at=now - timedelta(minutes=1))
    _create_question(db, user_b, created_at=now)
    db.commit()

    response = auth_client.get("/history/questions", params={"limit": 1})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0] == {
        "id": newer.id,
        "material_id": newer.material_id,
        "subject": "algorithms",
        "question_text": "Question for algorithms",
        "answer": "Answer",
        "explanation": "Explanation",
        "concept": "Concept",
        "question_type": "short_answer",
        "difficulty": "medium",
        "created_at": newer.created_at.isoformat(),
    }
    assert data[0]["id"] != older.id


def test_wrong_answer_history_is_ordered_limited_and_user_scoped(
    auth_client,
    db,
    user_a,
    user_b,
):
    now = utc_now()
    items = [
        models.WrongAnswer(
            user_id=user_a.id,
            question_id=1,
            user_answer="Older",
            correct_answer="Answer",
            concept="BFS",
            is_correct=False,
            created_at=now - timedelta(minutes=2),
        ),
        models.WrongAnswer(
            user_id=user_a.id,
            question_id=2,
            user_answer="Newer",
            correct_answer="Answer",
            concept="DFS",
            is_correct=False,
            created_at=now - timedelta(minutes=1),
        ),
        models.WrongAnswer(
            user_id=user_b.id,
            question_id=3,
            user_answer="Other user",
            correct_answer="Answer",
            concept="SQL",
            is_correct=False,
            created_at=now,
        ),
    ]
    db.add_all(items)
    db.commit()

    response = auth_client.get("/history/wrong-answers", params={"limit": 1})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == items[1].id
    assert data[0]["user_answer"] == "Newer"
    assert "user_id" not in data[0]


def test_history_rejects_invalid_limit(auth_client):
    assert auth_client.get(
        "/history/questions", params={"limit": 0}
    ).status_code == 422
    assert auth_client.get(
        "/history/wrong-answers", params={"limit": 101}
    ).status_code == 422
