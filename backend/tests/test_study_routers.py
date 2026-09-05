from datetime import date, timedelta

import pytest

from app import models
from app.ai import study_ai
from app.services import material_service
from app.services.analytics import dashboard_service, report_service
from app.services.exceptions import (
    InvalidAIResponseError,
    InvalidRequestError,
    ResourceNotFoundError,
)
from app.services.recommendation import smart_review_service


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


def test_create_goal_returns_400_for_past_exam_date(auth_client):
    response = auth_client.post(
        "/study-goals",
        json={
            "subject": "algorithms",
            "title": "Past exam",
            "target_score": 90,
            "exam_date": (date.today() - timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 400


def test_create_session_returns_400_for_mismatched_goal_subject(
    auth_client,
    db,
    user_a,
):
    goal = _create_goal(db, user_a, subject="databases")

    response = auth_client.post(
        "/study-sessions",
        json={
            "subject": "algorithms",
            "goal_id": goal.id,
            "duration_minutes": 60,
            "content": "BFS",
            "focus_score": 4,
        },
    )

    assert response.status_code == 400


def test_generate_checklist_returns_502_for_invalid_ai_output(
    auth_client,
    db,
    user_a,
    monkeypatch,
):
    goal = _create_goal(db, user_a)
    monkeypatch.setattr(
        study_ai,
        "generate_study_checklist_items",
        lambda **kwargs: [{"title": "", "priority": 0}],
    )

    response = auth_client.post(
        "/study-checklists/generate",
        json={"goal_id": goal.id, "item_count": 1},
    )

    assert response.status_code == 502
    assert db.query(models.StudyChecklistItem).count() == 0


def test_generate_study_report_delegates_to_service(
    auth_client,
    db,
    user_a,
    monkeypatch,
):
    expected_result = {
        "attempt_summary": {"attempt_count": 1},
        "weak_concepts": [],
        "score_trend": [],
        "report": "Keep practicing.",
    }
    captured = {}

    def fake_generate_personal_report(**kwargs):
        captured.update(kwargs)
        return expected_result

    monkeypatch.setattr(
        report_service,
        "generate_personal_report",
        fake_generate_personal_report,
    )

    response = auth_client.post(
        "/study-reports/generate",
        json={"subject": "algorithms", "limit": 5},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "개인 맞춤 학습 리포트가 생성되었습니다.",
        **expected_result,
    }
    assert captured == {
        "db": db,
        "user_id": user_a.id,
        "user_name": user_a.user_name,
        "subject": "algorithms",
        "limit": 5,
    }


def test_generate_study_report_returns_404_when_attempts_do_not_exist(
    auth_client,
    monkeypatch,
):
    def raise_not_found(**kwargs):
        raise ResourceNotFoundError("학습 리포트를 생성할 응시 기록이 없습니다.")

    monkeypatch.setattr(
        report_service,
        "generate_personal_report",
        raise_not_found,
    )

    response = auth_client.post(
        "/study-reports/generate",
        json={},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "학습 리포트를 생성할 응시 기록이 없습니다.",
    }


def test_generate_weekly_report_delegates_to_service(
    auth_client,
    db,
    user_a,
    monkeypatch,
):
    expected_result = {
        "period_summary": {"days": 7},
        "session_summary": {"session_count": 0},
        "attempt_summary": {"attempt_count": 1},
        "weak_concepts": [],
        "checklist_summary": {"total_count": 0},
        "report": "Weekly feedback",
    }
    captured = {}

    def fake_generate_weekly_report(**kwargs):
        captured.update(kwargs)
        return expected_result

    monkeypatch.setattr(
        report_service,
        "generate_weekly_report",
        fake_generate_weekly_report,
    )

    response = auth_client.post(
        "/weekly-reports/generate",
        json={"subject": "algorithms", "days": 7},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "주간 학습 리포트가 생성되었습니다",
        **expected_result,
    }
    assert captured == {
        "db": db,
        "user_id": user_a.id,
        "user_name": user_a.user_name,
        "subject": "algorithms",
        "days": 7,
    }


def test_generate_weekly_report_returns_404_for_empty_period(
    auth_client,
    monkeypatch,
):
    def raise_not_found(**kwargs):
        raise ResourceNotFoundError(
            "주간 리포트를 생성할 학습 데이터가 없습니다."
        )

    monkeypatch.setattr(
        report_service,
        "generate_weekly_report",
        raise_not_found,
    )

    response = auth_client.post("/weekly-reports/generate", json={})

    assert response.status_code == 404
    assert response.json() == {
        "detail": "주간 리포트를 생성할 학습 데이터가 없습니다.",
    }


@pytest.mark.parametrize("days", [0, 32])
def test_generate_weekly_report_rejects_invalid_days(auth_client, days):
    response = auth_client.post(
        "/weekly-reports/generate",
        json={"days": days},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("path", "payload", "service_name"),
    [
        ("/home-dashboard", {"subject": "algorithms"}, "get_home_dashboard"),
        ("/goal-dashboard", {"goal_id": 42}, "get_goal_dashboard"),
    ],
)
def test_dashboard_routers_delegate_to_service(
    auth_client,
    user_a,
    monkeypatch,
    path,
    payload,
    service_name,
):
    captured = {}

    def fake_dashboard(**kwargs):
        captured.update(kwargs)
        return {"comment": "Dashboard feedback"}

    monkeypatch.setattr(dashboard_service, service_name, fake_dashboard)

    response = auth_client.post(path, json=payload)

    assert response.status_code == 200
    assert response.json()["comment"] == "Dashboard feedback"
    assert captured["user_id"] == user_a.id
    assert captured["user_name"] == user_a.user_name
    if path == "/home-dashboard":
        assert captured["subject"] == "algorithms"
    else:
        assert captured["goal_id"] == 42


@pytest.mark.parametrize(
    ("path", "payload", "service_name"),
    [
        ("/home-dashboard", {}, "get_home_dashboard"),
        ("/goal-dashboard", {"goal_id": 42}, "get_goal_dashboard"),
    ],
)
def test_dashboard_routers_translate_not_found_errors(
    auth_client,
    monkeypatch,
    path,
    payload,
    service_name,
):
    def raise_not_found(**kwargs):
        raise ResourceNotFoundError("대시보드 데이터가 없습니다.")

    monkeypatch.setattr(dashboard_service, service_name, raise_not_found)

    response = auth_client.post(path, json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": "대시보드 데이터가 없습니다."}


def test_save_smart_review_queue_returns_502_for_invalid_ai_output(
    auth_client,
    monkeypatch,
):
    def raise_invalid_ai_response(**kwargs):
        raise InvalidAIResponseError(
            "AI가 생성한 스마트 복습 항목 형식이 올바르지 않습니다."
        )

    monkeypatch.setattr(
        smart_review_service,
        "generate_and_save_queue",
        raise_invalid_ai_response,
    )

    response = auth_client.post(
        "/smart-review/queue/save",
        json={"limit": 5},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "AI가 생성한 스마트 복습 항목 형식이 올바르지 않습니다."
    }


@pytest.mark.parametrize("limit", [0, 11])
def test_save_smart_review_queue_rejects_invalid_limit(auth_client, limit):
    response = auth_client.post(
        "/smart-review/queue/save",
        json={"limit": limit},
    )

    assert response.status_code == 422


def test_extract_pdf_router_returns_service_result(
    auth_client,
    user_a,
    monkeypatch,
):
    monkeypatch.setattr(
        material_service,
        "extract_pdf",
        lambda **kwargs: {
            "material_id": 1,
            "subject": "algorithms",
            "filename": "notes.pdf",
        },
    )

    response = auth_client.post(
        "/materials/extract-pdf",
        data={"subject": "algorithms"},
        files={"file": ("notes.pdf", b"%PDF-fake", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "user_name": user_a.user_name,
        "material_id": 1,
        "subject": "algorithms",
        "filename": "notes.pdf",
    }


def test_extract_pdf_router_returns_400_for_invalid_pdf(
    auth_client,
    monkeypatch,
):
    def raise_invalid_request(**kwargs):
        raise InvalidRequestError("올바른 PDF 파일이 아닙니다.")

    monkeypatch.setattr(material_service, "extract_pdf", raise_invalid_request)

    response = auth_client.post(
        "/materials/extract-pdf",
        data={"subject": "algorithms"},
        files={"file": ("notes.pdf", b"invalid", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "올바른 PDF 파일이 아닙니다."}
