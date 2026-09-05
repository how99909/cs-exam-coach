from app import models
from app.ai import question_ai


def test_generate_questions_saves_material_and_questions(
    client,
    db,
    user_a,
    auth_as,
    monkeypatch,
):
    auth_as(user_a)
    
    monkeypatch.setattr(
        question_ai,
        "generate_questions",
        lambda **kwargs: [
            {
                "question_text": "BFS란 무엇인가?",
                "answer": "너비 우선 탐색",
                "explanation": "레벨 순서로 탐색한다.",
                "concept": "BFS",
                "question_type": "short_answer",
            },
            {
                "question_text": "DFS란 무엇인가?",
                "answer": "깊이 우선 탐색",
                "explanation": "한 경로를 깊게 탐색한다",
                "concept": "DFS",
                "question_type": "short_answer",
            },
        ],
    )
    
    response = client.post(
        "/questions/generate",
        json={
            "subject": "algorithms",
            "content": "BFS and DFS",
            "question_type": "short_answer",
            "count": 2,
            "difficulty": "medium",
        },
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert len(data["questions"]) == 2
    
    material = (
        db.query(models.StudyMaterial)
        .filter(
            models.StudyMaterial.id == data["material_id"]
        )
        .first()
    )
    
    assert material is not None
    assert material.user_id == user_a.id
    assert material.subject == "algorithms"
    
    questions = (
        db.query(models.Question)
        .filter(
            models.Question.material_id == material.id
        )
        .all()
    )
    
    assert len(questions) == 2
    assert {q.concept for q in questions} == {
        "BFS",
        "DFS",
    }