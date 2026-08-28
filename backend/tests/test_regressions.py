import pytest

from pydantic import ValidationError

from app.schemas import (
    QuestionGenerateRequest,
    StudySessionCreateRequest,
)


def test_analytics_is_not_captured_as_attempt_id(
    auth_client,
):
    response = auth_client.get(
        "/exam-attempts/analytics",
    )
    
    assert response.status_code == 200
    assert response.json()["attempt_count"] == 0


def test_query_limit_is_bounded(
    auth_client,
):
    response = auth_client.get(
        "/exam-attempts/history",
        params={"limit": 0},
    )
    
    assert response.status_code == 422


def test_question_count_is_bounded():
    with pytest.raises(ValidationError):
        QuestionGenerateRequest(
            subject="algorithm",
            content="content",
            count=0,
        )
        
        
def test_study_session_values_are_bounded():
    with pytest.raises(ValidationError):
        StudySessionCreateRequest(
            subject="algorithm",
            duration_minutes=0,
            content="review",
            focus_score=6,
        )
        
        
def test_register_rejects_password_over_72_utf8_bytes(client):
    password = "가" * 25
    
    response = client.post(
        "/auth/register",
        json={
            "user_name": "student1",
            "email": "student1@example.com",
            "password": password,
        },
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "비밀번호는 UTF-8 기준 72바이트 이하여야 합니다."
    )