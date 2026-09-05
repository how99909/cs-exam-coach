from datetime import date, timedelta

import pytest

from app import models
from app.ai import report_ai
from app.services.analytics import report_service
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.time_utils import utc_now


def _create_goal(db, user, *, subject="algorithms"):
    goal = models.StudyGoal(
        user_id=user.id, subject=subject, title="Exam", target_score=90,
        exam_date=date.today() + timedelta(days=7),
    )
    db.add(goal)
    db.flush()
    return goal


def _create_attempt(db, user, *, subject="algorithms", title="Exam", score=0, created_at=None):
    attempt = models.ExamAttempt(
        user_id=user.id, subject=subject, title=title, total_questions=10,
        correct_count=score // 10, score=score, created_at=created_at or utc_now(),
    )
    db.add(attempt)
    db.flush()
    return attempt


def test_personal_report_filters_orders_limits_and_passes_summary_to_ai(
    db, user_a, user_b, monkeypatch,
):
    now = utc_now()
    older = _create_attempt(
        db, user_a, title="Older", score=60, created_at=now - timedelta(days=2)
    )
    latest = _create_attempt(
        db, user_a, title="Latest", score=80, created_at=now - timedelta(days=1)
    )
    _create_attempt(db, user_a, subject="databases", score=100)
    _create_attempt(db, user_b, score=100)
    db.commit()
    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return "Personal report"

    monkeypatch.setattr(
        report_ai, 
        "generate_study_report", 
        fake_generate
    )
    result = report_service.generate_personal_report(
        db=db, user_id=user_a.id, user_name=user_a.user_name,
        subject="algorithms", limit=2,
    )

    assert result["attempt_summary"] == {
        "attempt_count": 2, "average_score": 70.0, "latest_score": 80,
        "best_score": 80, "lowest_score": 60,
    }
    assert [item["attempt_id"] for item in result["score_trend"]] == [
        older.id, latest.id,
    ]
    assert captured["user_name"] == user_a.user_name
    assert captured["subject"] == "algorithms"
    assert captured["attempt_summary"] == result["attempt_summary"]
    assert captured["score_trend"] == result["score_trend"]
    assert result["report"] == "Personal report"


def test_personal_report_rejects_empty_filtered_result(db, user_a):
    _create_attempt(db, user_a, subject="databases")
    db.commit()

    with pytest.raises(ResourceNotFoundError):
        report_service.generate_personal_report(
            db=db, user_id=user_a.id, user_name=user_a.user_name,
            subject="algorithms", limit=5,
        )


@pytest.mark.parametrize("days", [0, 32])
def test_weekly_report_rejects_days_outside_supported_range(db, user_a, days):
    with pytest.raises(InvalidRequestError):
        report_service.generate_weekly_report(
            db=db, user_id=user_a.id, user_name=user_a.user_name,
            subject=None, days=days,
        )


def test_weekly_report_only_counts_matching_checklist_activity_in_period(
    db, user_a, user_b, monkeypatch,
):
    now = utc_now()
    goal_a = _create_goal(db, user_a)
    database_goal = _create_goal(db, user_a, subject="databases")
    goal_b = _create_goal(db, user_b)
    db.add_all([
        models.StudyChecklistItem(
            user_id=user_a.id, goal_id=goal_a.id, subject="algorithms",
            title="Old pending", created_at=now - timedelta(days=30),
        ),
        models.StudyChecklistItem(
            user_id=user_a.id, goal_id=goal_a.id, subject="algorithms",
            title="Recently completed", is_done=True,
            created_at=now - timedelta(days=30), completed_at=now - timedelta(days=1),
        ),
        models.StudyChecklistItem(
            user_id=user_a.id, goal_id=goal_a.id, subject="algorithms",
            title="Recently created", created_at=now - timedelta(days=1),
        ),
        models.StudyChecklistItem(
            user_id=user_a.id, goal_id=database_goal.id, subject="databases",
            title="Other subject", created_at=now - timedelta(days=1),
        ),
        models.StudyChecklistItem(
            user_id=user_b.id, goal_id=goal_b.id, subject="algorithms",
            title="Other user", created_at=now - timedelta(days=1),
        ),
    ])
    db.commit()

    monkeypatch.setattr(report_service, "utc_now", lambda: now)
    monkeypatch.setattr(
        report_ai, 
        "generate_weekly_study_report",
        lambda **kwargs: "Weekly feedback",
    )
    result = report_service.generate_weekly_report(
        db=db, user_id=user_a.id, user_name=user_a.user_name,
        subject="algorithms", days=7,
    )

    assert result["checklist_summary"] == {
        "total_count": 2, "done_count": 1, "pending_count": 1,
        "progress_rate": 50.0,
    }
    assert result["period_summary"] == {
        "days": 7, "start_at": str(now - timedelta(days=7)), "end_at": str(now),
    }
    assert result["report"] == "Weekly feedback"


def test_weekly_report_rejects_empty_period(db, user_a, monkeypatch):
    now = utc_now()
    monkeypatch.setattr(report_service, "utc_now", lambda: now)

    with pytest.raises(ResourceNotFoundError):
        report_service.generate_weekly_report(
            db=db, user_id=user_a.id, user_name=user_a.user_name,
            subject=None, days=7,
        )
