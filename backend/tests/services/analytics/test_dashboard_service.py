from datetime import date, timedelta

import pytest

from app import models
from app.ai import dashboard_ai
from app.services.analytics import dashboard_service
from app.services.exceptions import ResourceNotFoundError
from app.time_utils import utc_now


def _create_goal(db, user, *, subject="algorithms"):
    goal = models.StudyGoal(
        user_id=user.id,
        subject=subject,
        title="Exam",
        target_score=90,
        exam_date=date.today() + timedelta(days=7),
    )
    db.add(goal)
    db.flush()
    return goal


def _create_wrong_answer(db, user, *, subject, concept):
    material = models.StudyMaterial(
        user_id=user.id,
        subject=subject,
        content=f"{concept} material",
    )
    db.add(material)
    db.flush()
    question = models.Question(
        material_id=material.id,
        question_text=f"Question about {concept}",
        answer="answer",
        concept=concept,
        question_type="short_answer",
        difficulty="medium",
    )
    db.add(question)
    db.flush()
    db.add(
        models.WrongAnswer(
            user_id=user.id,
            question_id=question.id,
            user_answer="wrong",
            correct_answer="answer",
            concept=concept,
        )
    )


def test_goal_dashboard_includes_five_most_recent_sessions(
    db,
    user_a,
    monkeypatch,
):
    goal = _create_goal(db, user_a)
    now = utc_now()
    sessions = []
    for index in range(6):
        session = models.StudySession(
            user_id=user_a.id,
            subject=goal.subject,
            goal_id=goal.id,
            duration_minutes=30,
            content=f"Session {index}",
            created_at=now - timedelta(minutes=index),
        )
        db.add(session)
        sessions.append(session)
    db.commit()

    monkeypatch.setattr(
        dashboard_ai,
        "generate_goal_dashboard_comment",
        lambda **kwargs: "Goal feedback",
    )

    result = dashboard_service.get_goal_dashboard(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        goal_id=goal.id,
    )

    recent_sessions = result["session_summary"]["recent_sessions"]
    assert len(recent_sessions) == 5
    assert [item["id"] for item in recent_sessions] == [
        session.id for session in sessions[:5]
    ]


def test_home_dashboard_filters_cumulative_weak_concepts_by_user_and_subject(
    db,
    user_a,
    user_b,
    monkeypatch,
):
    _create_wrong_answer(db, user_a, subject="algorithms", concept="BFS")
    _create_wrong_answer(db, user_a, subject="algorithms", concept="BFS")
    _create_wrong_answer(db, user_a, subject="databases", concept="SQL")
    _create_wrong_answer(db, user_b, subject="algorithms", concept="DFS")
    db.commit()

    monkeypatch.setattr(
        dashboard_ai,
        "generate_home_dashboard_comment",
        lambda **kwargs: "Home feedback",
    )

    result = dashboard_service.get_home_dashboard(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        subject="algorithms",
    )

    assert result["weak_concepts"] == [
        {"concept": "BFS", "wrong_count": 2}
    ]
    assert result["session_summary"]["period_days"] == 7
    assert result["comment"] == "Home feedback"


def test_goal_dashboard_rejects_another_users_goal(db, user_a, user_b):
    goal = _create_goal(db, user_b)
    db.commit()

    with pytest.raises(ResourceNotFoundError):
        dashboard_service.get_goal_dashboard(
            db=db,
            user_id=user_a.id,
            user_name=user_a.user_name,
            goal_id=goal.id,
        )


def test_goal_dashboard_passes_goal_to_ai(
    db,
    user_a,
    monkeypatch,
):
    captured = {}
    
    goal = _create_goal(
        db=db,
        user=user_a,
    )
    
    def fake_comment(**kwargs):
        captured.update(kwargs)
        return "comment"
    
    monkeypatch.setattr(
        dashboard_ai,
        "generate_goal_dashboard_comment",
        fake_comment,
    )
    
    result = dashboard_service.get_goal_dashboard(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        goal_id=goal.id
    )
    
    assert "goal" in captured
    assert captured["goal"]["id"] == goal.id
    