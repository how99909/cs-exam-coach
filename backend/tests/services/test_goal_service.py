from datetime import date, timedelta

import pytest

from app import models
from app.ai import study_ai
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.services.study import goal_service
from app.time_utils import utc_now


def _create_goal(
    db,
    user,
    *,
    subject="algorithms",
    exam_date=None,
):
    goal = models.StudyGoal(
        user_id=user.id,
        subject=subject,
        title="Exam",
        target_score=100,
        exam_date=exam_date or date.today() + timedelta(days=7),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def test_create_goal_saves_goal(db, user_a):
    exam_date = date.today() + timedelta(days=7)

    goal = goal_service.create_goal(
        db=db,
        user_id=user_a.id,
        subject="algorithms",
        title="Final exam",
        target_score=95,
        exam_date=exam_date,
    )

    assert goal.id is not None
    assert goal.user_id == user_a.id
    assert goal.exam_date == exam_date
    assert db.query(models.StudyGoal).count() == 1


def test_create_goal_rejects_past_exam_date(db, user_a):
    with pytest.raises(InvalidRequestError):
        goal_service.create_goal(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            title="Past exam",
            target_score=90,
            exam_date=date.today() - timedelta(days=1),
        )

    assert db.query(models.StudyGoal).count() == 0


def test_list_goals_filters_user_and_subject_and_orders_by_exam_date(
    db,
    user_a,
    user_b,
):
    later = _create_goal(
        db,
        user_a,
        exam_date=date.today() + timedelta(days=14),
    )
    earlier = _create_goal(
        db,
        user_a,
        exam_date=date.today() + timedelta(days=3),
    )
    _create_goal(db, user_a, subject="databases")
    _create_goal(db, user_b)

    goals = goal_service.list_goals(
        db=db,
        user_id=user_a.id,
        subject="algorithms",
    )

    assert [goal.id for goal in goals] == [earlier.id, later.id]

def test_goal_queries_own_status(
    db,
    user_a,
):
    goal_a = models.StudyGoal(
        user_id=user_a.id,
        subject="algorithms",
        title="Exam",
        target_score=100,
        exam_date=date.today() + timedelta(days=7),
    )
    
    db.add(goal_a)
    db.commit()
    
    result = goal_service.get_goal_status(
        db=db,
        user_id=user_a.id,
        goal_id=goal_a.id,
    )
    
    assert result is not None
    assert result["goal"] is not None
    assert result["goal"]["subject"] == "algorithms"
    assert result["current_status"] is not None
    assert result["current_status"]["target_score"] == 100
    assert result["current_status"]["attempt_count"] == 0
    assert result["current_status"]["score_gap"] is None
    
    
def test_goal_rejects_other_users_status(
    db,
    user_a,
    user_b,
):
    goal_b = models.StudyGoal(
        user_id=user_b.id,
        subject="algorithms",
        title="Exam",
        target_score=90,
        exam_date=date.today() + timedelta(days=7),
    )
    
    db.add(goal_b)
    db.commit()
    
    with pytest.raises(
        ResourceNotFoundError
    ):
        goal_service.get_goal_status(
            db=db,
            user_id=user_a.id,
            goal_id=goal_b.id,
        )


def test_goal_status_calculates_scores_and_weak_concepts(db, user_a):
    goal = _create_goal(db, user_a)
    material = models.StudyMaterial(
        user_id=user_a.id,
        subject="algorithms",
        content="BFS and DFS",
    )
    db.add(material)
    db.flush()
    question = models.Question(
        material_id=material.id,
        question_text="Which structure does BFS use?",
        answer="Queue",
        explanation="FIFO",
        concept="BFS",
        question_type="short_answer",
        difficulty="medium",
    )
    db.add(question)
    db.flush()

    now = utc_now()
    older_attempt = models.ExamAttempt(
        user_id=user_a.id,
        subject="algorithms",
        title="Attempt 1",
        total_questions=1,
        correct_count=0,
        score=60,
        created_at=now - timedelta(minutes=1),
    )
    latest_attempt = models.ExamAttempt(
        user_id=user_a.id,
        subject="algorithms",
        title="Attempt 2",
        total_questions=1,
        correct_count=1,
        score=80,
        created_at=now,
    )
    db.add_all([older_attempt, latest_attempt])
    db.flush()
    db.add(
        models.ExamAttemptAnswer(
            attempt_id=latest_attempt.id,
            question_id=question.id,
            user_answer="Stack",
            is_correct=False,
            feedback="Review queues",
        )
    )
    db.commit()

    result = goal_service.get_goal_status(
        db=db,
        user_id=user_a.id,
        goal_id=goal.id,
    )

    assert result["current_status"]["attempt_count"] == 2
    assert result["current_status"]["current_average_score"] == 70.0
    assert result["current_status"]["latest_score"] == 80
    assert result["current_status"]["score_gap"] == 30.0
    assert result["weak_concepts"] == [{"concept": "BFS", "wrong_count": 1}]


def test_generate_goal_strategy_passes_status_to_ai(
    db,
    user_a,
    monkeypatch,
):
    goal = _create_goal(db, user_a)
    captured = {}

    def fake_generate_goal_strategy(**kwargs):
        captured.update(kwargs)
        return {"summary": "Keep reviewing BFS"}

    monkeypatch.setattr(
        study_ai,
        "generate_goal_strategy",
        fake_generate_goal_strategy,
    )

    result = goal_service.generate_goal_strategy(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        goal_id=goal.id,
    )

    assert captured["user_name"] == user_a.user_name
    assert captured["goal"]["id"] == goal.id
    assert captured["current_status"]["target_score"] == 100
    assert captured["weak_concepts"] == []
    assert result["strategy"] == {"summary": "Keep reviewing BFS"}
