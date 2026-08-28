from app import models, rag_service, ai_service


def test_rag_index_users_authenticated_user(
    client,
    db,
    user_a,
    auth_as,
    monkeypatch,
):
    material = models.StudyMaterial(
        user_id=user_a.id,
        subject="algorithms",
        content="BFS",
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    auth_as(user_a)
    
    captured = {}
    
    def fake_index_document(
        user_name,
        subject,
        material_id,
        content,
    ):
        captured["user_name"] = user_name
        captured["subject"] = subject
        captured["material_id"] = material_id
        
        return {
            "success": True,
            "chunk_count": 1,
            "material_id": material_id,
        }
        
    monkeypatch.setattr(
        rag_service,
        "index_document",
        fake_index_document,
    )
    
    response = client.post(
        "/rag/index",
        json={
            "subject": "algorithms",
            "material_id": material.id,
            "content": "BFS content",
        },
    )
    
    assert response.status_code == 200
    
    assert captured["user_name"] == user_a.user_name
    assert captured["material_id"] == material.id
    
    
def test_rag_ask_uses_authenticated_user(
    client,
    db,
    user_a,
    auth_as,
    monkeypatch,
):
    material = models.StudyMaterial(
        user_id=user_a.id,
        subject="algorithms",
        content="BFS",
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    auth_as(user_a)
    
    captured = {}
    
    def fake_answer_with_context(
        user_name,
        subject,
        question,
        top_k,
        material_id,
    ):
        captured["user_name"] = user_name
        captured["material_id"] = material_id
        
        return {
            "success": True,
            "answer": "BFS uses a queue.",
            "sources": [],
            "material_id": material_id,
            "search_scope": "test",
        }
        
    monkeypatch.setattr(
        rag_service,
        "answer_with_context",
        fake_answer_with_context,
    )
    
    response = client.post(
        "/rag/ask",
        json={
            "subject": "algorithms",
            "material_id": material.id,
            "question": "What is BFS?",
            "top_k": 5,
        },
    )
    
    assert response.status_code == 200
    
    assert response.json()["answer"] == (
        "BFS uses a queue."
    )
    
    assert captured["user_name"] == user_a.user_name
    
    
def test_rag_question_generation_saves_question(
    client,
    db,
    user_a,
    auth_as,
    monkeypatch,
):
    material = models.StudyMaterial(
        user_id=user_a.id,
        subject="algorithms",
        content="BFS",
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    auth_as(user_a)
    
    monkeypatch.setattr(
        rag_service,
        "get_document_chunks_for_question_generation",
        lambda **kwargs: [
            {
                "content": "BFS uses queue.",
                "metadata": {
                    "user_name": user_a.user_name,
                    "subject": "algorithms",
                    "material_id": material.id,
                    "chunk_index": 0,
                },
            }
        ],
    )
    
    monkeypatch.setattr(
        ai_service,
        "generate_question_from_rag_chunks",
        lambda **kwargs: [
            {
                "question": "BFS의 자료구조는?",
                "answer": "Queue",
                "explanation": "FIFO",
                "concept": "BFS",
                "source": "chunk 0",
            }
        ],
    )
    
    response = client.post(
        "/rag-questions/generate",
        json={
            "subject": "algorithms",
            "material_id": material.id,
            "count": 1,
            "top_k": 5,
            "difficulty": "medium",
            "question_type": "short_answer",
        },
    )
    
    assert response.status_code == 200
    
    question_id = response.json()["questions"][0]["id"]
    
    question = db.get(
        models.Question,
        question_id,
    )
    
    assert question is not None
    assert question.material_id == material.id
    assert question.concept == "BFS"