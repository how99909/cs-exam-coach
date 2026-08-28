from datetime import date, timedelta

from app import models


def create_material(
    db,
    user,
    subject="algorithms",
    content="graph algorithms"
):
    material = models.StudyMaterial(
        user_id=user.id,
        subject=subject,
        content=content,
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    return material


def create_question(
    db,
    material,
):
    question = models.Question(
        material_id=material.id,
        question_text="What is BFS?",
        answer="Breadth-first search",
        explanation="BFS explores level by level.",
        concept="BFS",
        question_type="short_answer",
        difficulty="medium",
    )
    
    db.add(question)
    db.commit()
    db.refresh(question)
    
    return question


def create_goal(
    db,
    user,
    subject="algorithms",
):
    goal = models.StudyGoal(
        user_id=user.id,
        subject=subject,
        title="Algorithms exam",
        target_score=90,
        exam_date=date.today() + timedelta(days=7),
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    return goal


def create_attempt(
    db,
    user,
    subject="algorithms",
):
    attempt = models.ExamAttempt(
        user_id=user.id,
        subject=subject,
        title="Practice exam",
        total_questions=1,
        correct_count=1,
        score=100,
    )
    
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    return attempt


def test_user_cannot_grade_another_users_question(
    client,
    db,
    user_a,
    user_b,
    auth_as,
):
    material_b = create_material(
        db,
        user_b,
    )
    question_b = create_question(
        db,
        material_b,
    )
    
    auth_as(user_a)
    
    response = client.post(
        "/grading/grade",
        json={
            "question_id": question_b.id,
            "user_answer": "test",
        },
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == (
        "문제를 찾을 수 없습니다."
    )
    
    
def test_user_cannot_submit_another_users_question(
    client,
    db,
    user_a,
    user_b,
    auth_as,
):
    material_b = create_material(db, user_b)
    question_b = create_question(db, material_b)
    
    auth_as(user_a)
    
    response = client.post(
        "/exam-attempts/submit",
        json={
            "subject": "algorithms",
            "title": "Unauthorized exam",
            "answers": [
                {
                    "question_id": question_b.id,
                    "user_answer": "answer",
                }
            ],
        },
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == (
        "일부 문제를 찾지 못했습니다."
    )
    
    
def test_user_cannot_view_another_users_attempt(
    client,
    db,
    user_a,
    user_b,
    auth_as,
):
    attempt_b = create_attempt(
        db,
        user_b,
    )
    
    auth_as(user_a)
    
    response = client.get(
        f"/exam-attempts/{attempt_b.id}"
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == (
        "응시 기록을 찾지 못했습니다."
    )
    
    
def test_attempt_history_only_returns_current_user(
    client,
    db,
    user_a,
    user_b,
    auth_as,
):
    attempt_a = create_attempt(
        db,
        user_a,
    )
    
    create_attempt(
        db,
        user_b,
    )
    
    auth_as(user_a)
    
    response = client.get(
        "/exam-attempts/history"
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["attempt_count"] == 1
    assert len(data["attempts"]) == 1
    assert data["attempts"][0]["id"] == attempt_a.id
    
    
def test_user_cannot_view_another_users_goal(
    client,
    db,
    user_a,
    user_b,
    auth_as,
):
    goal_b = create_goal(
        db,
        user_b,
    )
    
    auth_as(user_a)
    
    response = client.get(
        f"/study-goals/{goal_b.id}/status"
    )
    
    assert response.status_code == 404
    
    
def test_user_can_view_own_goal(
    client,
    db,
    user_a,
    auth_as,
):
    goal = create_goal(
        db,
        user_a,
    )
    
    auth_as(user_a)
    
    response = client.get(
        f"/study-goals/{goal.id}/status"
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["goal"]["id"] == goal.id
    assert data["goal"]["subject"] == "algorithms"
    
    
def test_goal_list_only_returns_current_user(
    client,
    db,
    user_a,
    user_b,
    auth_as,
):
    goal_a = create_goal(
        db,
        user_a,
    )
    
    create_goal(
        db,
        user_b,
    )
    
    auth_as(user_a)
    
    response = client.get(
        "/study-goals"
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["goal_count"] == 1
    assert data["goals"][0]["id"] == goal_a.id
    
    
def test_user_cannot_rag_ask_another_users_material(
    client,
    db,
    user_a,
    user_b,
    auth_as,
):
    material_b = create_material(
        db,
        user_b,
    )
    
    auth_as(user_a)
    
    response = client.post(
        "/rag/ask",
        json={
            "subject": "algorithms",
            "material_id": material_b.id,
            "question": "Explain BFS.",
            "top_k": 5,
        },
    )
    
    assert response.status_code == 404
    
    
def test_user_cannot_index_another_users_material(
    client,
    db,
    user_a,
    user_b,
    auth_as,
):
    material_b = create_material(
        db,
        user_b,
    )
    
    auth_as(user_a)
    
    response = client.post(
        "/rag/index",
        json={
            "subject": "algorithms",
            "material_id": material_b.id,
            "content": "BFS content",
        },
    )
    
    assert response.status_code == 404
    
    
def test_user_cannot_delete_another_users_rag_document(
    client,
    db,
    user_a,
    user_b,
    auth_as,
):
    material_b = create_material(
        db,
        user_b,
    )
    
    auth_as(user_a)
    
    response = client.request(
        "DELETE",
        "/rag/documents",
        json={
            "subject": "algorithms",
            "material_id": material_b.id,
        },
    )
    
    assert response.status_code == 404