from types import SimpleNamespace

from app import models
from app.services.analytics import metrics_service


def test_build_checklist_summary_calculates_counts_and_progress():
    items = [
        SimpleNamespace(is_done=True),
        SimpleNamespace(is_done=False),
        SimpleNamespace(is_done=True),
    ]

    assert metrics_service.build_checklist_summary(items) == {
        "total_count": 3, "done_count": 2, "pending_count": 1,
        "progress_rate": 66.67,
    }


def test_build_checklist_summary_handles_empty_items():
    assert metrics_service.build_checklist_summary([]) == {
        "total_count": 0, "done_count": 0, "pending_count": 0,
        "progress_rate": 0,
    }


def test_build_session_summary_ignores_missing_focus_scores():
    sessions = [
        SimpleNamespace(duration_minutes=30, focus_score=3),
        SimpleNamespace(duration_minutes=60, focus_score=None),
        SimpleNamespace(duration_minutes=90, focus_score=5),
    ]

    assert metrics_service.build_session_summary(sessions) == {
        "session_count": 3, "total_minutes": 180, "total_hours": 3.0,
        "avg_focus_score": 4.0,
    }


def test_get_weak_concepts_from_attempts_aggregates_only_wrong_answers(db, user_a):
    material = models.StudyMaterial(
        user_id=user_a.id, subject="algorithms", content="Graphs",
    )
    db.add(material)
    db.flush()
    bfs = models.Question(
        material_id=material.id, question_text="BFS?", answer="Queue",
        concept="BFS", question_type="short_answer", difficulty="medium",
    )
    dfs = models.Question(
        material_id=material.id, question_text="DFS?", answer="Stack",
        concept="DFS", question_type="short_answer", difficulty="medium",
    )
    db.add_all([bfs, dfs])
    db.flush()
    attempt = models.ExamAttempt(
        user_id=user_a.id, subject="algorithms", title="Exam",
        total_questions=3, correct_count=1, score=33,
    )
    db.add(attempt)
    db.flush()
    db.add_all([
        models.ExamAttemptAnswer(
            attempt_id=attempt.id, question_id=bfs.id,
            user_answer="Wrong", is_correct=False,
        ),
        models.ExamAttemptAnswer(
            attempt_id=attempt.id, question_id=bfs.id,
            user_answer="Wrong again", is_correct=False,
        ),
        models.ExamAttemptAnswer(
            attempt_id=attempt.id, question_id=dfs.id,
            user_answer="Stack", is_correct=True,
        ),
    ])
    db.commit()

    assert metrics_service.get_weak_concepts_from_attempts(
        db=db, attempt_ids=[attempt.id], limit=10,
    ) == [{"concept": "BFS", "wrong_count": 2}]


def test_get_weak_concepts_from_attempts_handles_empty_ids(db):
    assert metrics_service.get_weak_concepts_from_attempts(
        db=db, attempt_ids=[],
    ) == []


def test_get_weak_concepts_from_wrong_answers_filters_user_and_subject(
    db, user_a, user_b,
):
    materials = [
        models.StudyMaterial(
            user_id=user_a.id, subject="algorithms", content="Graphs",
        ),
        models.StudyMaterial(
            user_id=user_a.id, subject="databases", content="SQL",
        ),
    ]
    db.add_all(materials)
    db.flush()
    questions = [
        models.Question(
            material_id=materials[0].id, question_text="BFS?", answer="Queue",
            concept="BFS", question_type="short_answer", difficulty="medium",
        ),
        models.Question(
            material_id=materials[1].id, question_text="SQL?", answer="Query",
            concept="SQL", question_type="short_answer", difficulty="medium",
        ),
    ]
    db.add_all(questions)
    db.flush()
    db.add_all([
        models.WrongAnswer(
            user_id=user_a.id, question_id=questions[0].id,
            user_answer="Wrong", correct_answer="Queue", concept="BFS",
        ),
        models.WrongAnswer(
            user_id=user_a.id, question_id=questions[1].id,
            user_answer="Wrong", correct_answer="Query", concept="SQL",
        ),
        models.WrongAnswer(
            user_id=user_b.id, question_id=questions[0].id,
            user_answer="Wrong", correct_answer="Queue", concept="BFS",
        ),
    ])
    db.commit()

    assert metrics_service.get_weak_concepts_from_wrong_answers(
        db=db, user_id=user_a.id, subject="algorithms", limit=5,
    ) == [{"concept": "BFS", "wrong_count": 1}]
