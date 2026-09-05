import pytest

from app.ai import dashboard_ai, openai_client, recommendation_ai, report_ai, study_ai


@pytest.fixture(autouse=True)
def disable_openai_client(monkeypatch):
    """Keep fallback tests deterministic and free of external API calls."""
    monkeypatch.setattr(openai_client, "client", None)


def test_smart_review_fallback_returns_valid_queue_item():
    result = recommendation_ai.generate_smart_review_queue_items(
        user_name="user_a",
        subject="algorithms",
        weak_concepts=[],
        recent_wrong_answers=[],
        pending_checklists=[],
        session_summary={},
        attempt_summary={},
        limit=5,
    )

    assert result
    assert {
        "title", "reason", "action", "estimated_minutes", "priority", "source_type"
    } <= result[0].keys()
    assert isinstance(result[0]["estimated_minutes"], int)
    assert isinstance(result[0]["priority"], int)


def test_study_checklist_fallback_returns_valid_item():
    result = study_ai.generate_study_checklist_items(
        goal={}, current_status={}, weak_concepts=[], item_count=5
    )

    assert result
    assert {"title", "description", "priority"} <= result[0].keys()
    assert isinstance(result[0]["priority"], int)


@pytest.mark.parametrize(
    ("generator", "kwargs"),
    [
        (study_ai.generate_goal_strategy, {
            "user_name": "user_a", "goal": {}, "current_status": {}, "weak_concepts": []
        }),
        (report_ai.generate_study_report, {
            "user_name": "user_a", "subject": "algorithms", "attempt_summary": {},
            "weak_concepts": [], "score_trend": []
        }),
        (report_ai.generate_weekly_study_report, {
            "user_name": "user_a", "subject": "algorithms", "period_summary": {},
            "session_summary": {}, "attempt_summary": {}, "weak_concepts": [],
            "checklist_summary": {}
        }),
        (dashboard_ai.generate_goal_dashboard_comment, {
            "user_name": "user_a", "goal": {}, "checklist_summary": {},
            "session_summary": {}, "attempt_summary": {}, "weak_concepts": []
        }),
        (dashboard_ai.generate_home_dashboard_comment, {
            "user_name": "user_a", "subject": "algorithms", "goal_summary": {},
            "session_summary": {}, "attempt_summary": {}, "review_queue_summary": {},
            "checklist_summary": {}, "weak_concepts": []
        }),
    ],
    ids=["goal-strategy", "study-report", "weekly-report", "goal-dashboard", "home-dashboard"],
)
def test_text_fallbacks_return_non_empty_strings(generator, kwargs):
    result = generator(**kwargs)

    assert isinstance(result, str)
    assert result.strip()
