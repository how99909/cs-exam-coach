from datetime import date, timedelta

from app import models


def test_goal_and_atudy_session_flow(
    client,
    db,
    user_a,
    auth_as,
):
    auth_as(user_a)
    
    goal_response = client.post(
        "/study-goals",
        json={
            "subject": "algorithms",
            "title": "중간고사 90점",
            "target_score": 90,
            "exam_date": (date.today() + timedelta(days=7)).isoformat(),
        },
    )
    
    assert goal_response.status_code == 200
    
    goal_id = goal_response.json()["goal"]["id"]
    
    session_response = client.post(
        "/study-sessions",
        json={
            "subject": "algorithms",
            "goal_id": goal_id,
            "duration_minutes": 60,
            "content": "BFS와 DFS 복습",
            "reflection": "BFS를 더 복습해야 함",
            "focus_score": 4,
        },
    )
    
    assert session_response.status_code == 200
    
    session = (
        db.query(models.StudySession)
        .filter(
            models.StudySession.goal_id == goal_id
        )
        .first()
    )
    
    assert session is not None
    assert session.user_id == user_a.id
    assert session.duration_minutes == 60
    
    summary_response = client.get(
        "/study-sessions/summary",
    )
    
    assert summary_response.status_code == 200
    
    summary = summary_response.json()
    
    assert summary["session_count"] == 1
    assert summary["total_minutes"] == 60
    assert summary["total_hours"] == 1.0
    assert summary["avg_focus_score"] == 4.0