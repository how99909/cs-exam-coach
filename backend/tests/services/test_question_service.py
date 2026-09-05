from app import models
from app.ai import question_ai
from app.services import question_service


def test_question_service_saves_result(
    db,
    user_a,
    monkeypatch,
):
    monkeypatch.setattr(
        question_ai,
        "generate_questions",
        lambda **kwargs: [
            {
                "question_text": "What is BFS?",
                "answer": "Breadth-first search",
                "explanation": "It explores nodes level by level.",
                "concept": "BFS",
                "question_type": "short_answer",
            },
            {
                "question_text": "What is DFS?",
                "answer": "Depth-first search",
                "explanation": "It explores one path as deeply as possible.",
                "concept": "DFS",
                "question_type": "short_answer",
            },
        ],
    )

    material, questions = question_service.generate_questions(
        db=db,
        user_id=user_a.id,
        subject="algorithms",
        content="BFS and DFS",
        question_type="short_answer",
        count=2,
        difficulty="medium",
    )

    saved_material = (
        db.query(models.StudyMaterial)
        .filter(models.StudyMaterial.id == material.id)
        .first()
    )

    assert saved_material is not None
    assert saved_material.user_id == user_a.id
    assert saved_material.subject == "algorithms"
    assert saved_material.content == "BFS and DFS"

    saved_questions = (
        db.query(models.Question)
        .filter(models.Question.material_id == material.id)
        .all()
    )

    assert len(questions) == 2
    assert len(saved_questions) == 2
    assert {question.concept for question in saved_questions} == {
        "BFS",
        "DFS",
    }
    assert all(
        question.difficulty == "medium"
        for question in saved_questions
    )
