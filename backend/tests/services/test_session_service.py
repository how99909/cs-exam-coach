from datetime import date, timedelta

import pytest

from app import models
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.services.study import session_service
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
    db.commit()
    db.refresh(goal)
    return goal


def _create_checklist_item(db, user, goal):
    item = models.StudyChecklistItem(
        user_id=user.id,
        goal_id=goal.id,
        subject=goal.subject,
        title="Review BFS",
        priority=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _create_session(
    db,
    user,
    *,
    subject="algorithms",
    goal_id=None,
    duration_minutes=60,
    focus_score=None,
    created_at=None,
):
    session = models.StudySession(
        user_id=user.id,
        subject=subject,
        goal_id=goal_id,
        duration_minutes=duration_minutes,
        content="Study content",
        focus_score=focus_score,
        created_at=created_at or utc_now(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def test_create_session_saves_all_fields(db, user_a):
    goal = _create_goal(db, user_a)
    item = _create_checklist_item(db, user_a, goal)

    session = session_service.create_session(
        db=db,
        user_id=user_a.id,
        subject="algorithms",
        goal_id=goal.id,
        checklist_item_id=item.id,
        duration_minutes=60,
        content="BFS",
        reflection="Review queues again",
        focus_score=4,
    )

    assert session.id is not None
    assert session.user_id == user_a.id
    assert session.subject == "algorithms"
    assert session.goal_id == goal.id
    assert session.checklist_item_id == item.id
    assert session.duration_minutes == 60
    assert session.content == "BFS"
    assert session.reflection == "Review queues again"
    assert session.focus_score == 4
    assert session.created_at is not None


@pytest.mark.parametrize("duration_minutes", [0, -1])
def test_create_session_rejects_non_positive_duration(
    db, user_a, duration_minutes
):
    with pytest.raises(InvalidRequestError):
        session_service.create_session(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            goal_id=None,
            checklist_item_id=None,
            duration_minutes=duration_minutes,
            content="BFS",
            reflection=None,
            focus_score=None,
        )


@pytest.mark.parametrize("focus_score", [0, 6])
def test_create_session_rejects_focus_score_outside_range(
    db, user_a, focus_score
):
    with pytest.raises(InvalidRequestError):
        session_service.create_session(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            goal_id=None,
            checklist_item_id=None,
            duration_minutes=30,
            content="BFS",
            reflection=None,
            focus_score=focus_score,
        )


@pytest.mark.parametrize("focus_score", [None, 1, 5])
def test_create_session_accepts_valid_focus_score_boundaries(
    db, user_a, focus_score
):
    session = session_service.create_session(
        db=db,
        user_id=user_a.id,
        subject="algorithms",
        goal_id=None,
        checklist_item_id=None,
        duration_minutes=30,
        content="BFS",
        reflection=None,
        focus_score=focus_score,
    )

    assert session.focus_score == focus_score


def test_session_rejects_other_users_goal(db, user_a, user_b):
    goal_b = _create_goal(db, user_b)

    with pytest.raises(ResourceNotFoundError):
        session_service.create_session(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            goal_id=goal_b.id,
            checklist_item_id=None,
            duration_minutes=60,
            content="BFS",
            reflection=None,
            focus_score=4,
        )


def test_session_rejects_other_users_checklist_item(db, user_a, user_b):
    goal_b = _create_goal(db, user_b)
    item_b = _create_checklist_item(db, user_b, goal_b)

    with pytest.raises(ResourceNotFoundError):
        session_service.create_session(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            goal_id=None,
            checklist_item_id=item_b.id,
            duration_minutes=60,
            content="BFS",
            reflection=None,
            focus_score=4,
        )


def test_session_rejects_goal_with_different_subject(db, user_a):
    goal = _create_goal(db, user_a, subject="databases")

    with pytest.raises(InvalidRequestError):
        session_service.create_session(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            goal_id=goal.id,
            checklist_item_id=None,
            duration_minutes=60,
            content="BFS",
            reflection=None,
            focus_score=4,
        )


def test_session_rejects_checklist_item_with_different_subject(db, user_a):
    goal = _create_goal(db, user_a, subject="databases")
    item = _create_checklist_item(db, user_a, goal)

    with pytest.raises(InvalidRequestError):
        session_service.create_session(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            goal_id=None,
            checklist_item_id=item.id,
            duration_minutes=60,
            content="BFS",
            reflection=None,
            focus_score=4,
        )


def test_session_rejects_checklist_item_from_another_goal(db, user_a):
    goal_a = _create_goal(db, user_a)
    goal_b = _create_goal(db, user_a)
    item_b = _create_checklist_item(db, user_a, goal_b)

    with pytest.raises(InvalidRequestError):
        session_service.create_session(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            goal_id=goal_a.id,
            checklist_item_id=item_b.id,
            duration_minutes=60,
            content="BFS",
            reflection=None,
            focus_score=4,
        )


def test_list_sessions_filters_orders_and_limits(db, user_a, user_b):
    goal_a = _create_goal(db, user_a)
    other_goal = _create_goal(db, user_a)
    now = utc_now()
    older = _create_session(
        db,
        user_a,
        goal_id=goal_a.id,
        created_at=now - timedelta(minutes=2),
    )
    newer = _create_session(
        db,
        user_a,
        goal_id=goal_a.id,
        created_at=now - timedelta(minutes=1),
    )
    _create_session(db, user_a, subject="databases", goal_id=other_goal.id)
    _create_session(db, user_b)

    sessions = session_service.list_sessions(
        db=db,
        user_id=user_a.id,
        subject="algorithms",
        goal_id=goal_a.id,
        limit=1,
    )

    assert [session.id for session in sessions] == [newer.id]
    assert older.id not in [session.id for session in sessions]


def test_session_summary_filters_subject_and_aggregates_own_data(
    db, user_a, user_b
):
    _create_session(db, user_a, duration_minutes=30, focus_score=3)
    _create_session(db, user_a, duration_minutes=90, focus_score=5)
    _create_session(
        db,
        user_a,
        subject="databases",
        duration_minutes=300,
        focus_score=1,
    )
    _create_session(db, user_b, duration_minutes=600, focus_score=1)

    result = session_service.get_session_summary(
        db=db,
        user_id=user_a.id,
        subject="algorithms",
    )

    assert result["session_count"] == 2
    assert result["total_minutes"] == 120
    assert result["total_hours"] == 2.0
    assert result["avg_focus_score"] == 4.0
    assert result["subject_summary"] == [
        {
            "subject": "algorithms",
            "session_count": 2,
            "total_minutes": 120,
            "total_hours": 2.0,
            "avg_focus_score": 4.0,
        }
    ]


def test_empty_session_summary(db, user_a):
    result = session_service.get_session_summary(db=db, user_id=user_a.id)

    assert result == {
        "session_count": 0,
        "total_minutes": 0,
        "total_hours": 0.0,
        "avg_focus_score": None,
        "subject_summary": [],
    }


def test_create_session_rolls_back_when_commit_fails(db, user_a, monkeypatch):
    original_rollback = db.rollback
    rollback_called = False

    def fail_commit():
        raise RuntimeError("commit failed")

    def track_rollback():
        nonlocal rollback_called
        rollback_called = True
        original_rollback()

    monkeypatch.setattr(db, "commit", fail_commit)
    monkeypatch.setattr(db, "rollback", track_rollback)

    with pytest.raises(RuntimeError, match="commit failed"):
        session_service.create_session(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            goal_id=None,
            checklist_item_id=None,
            duration_minutes=60,
            content="BFS",
            reflection=None,
            focus_score=4,
        )

    assert rollback_called is True
