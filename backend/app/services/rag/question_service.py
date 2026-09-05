from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, rag_service
from app.ai import question_ai
from app.services.exceptions import ResourceNotFoundError


def generate_rag_questions(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    subject: str,
    material_id: int | None = None,
    question_type: str = "short_answer",
    difficulty: str = "medium",
    count: int = 5,
    top_k: int = 8,
):      
    chunks = rag_service.get_document_chunks_for_question_generation(
        user_name=user_name,
        subject=subject,
        material_id=material_id,
        limit=top_k,
    )
    
    if not chunks:
        raise ResourceNotFoundError(
            "문제 생성을 위한 RAG 문서 chunk를 찾지 못했습니다. 먼저 PDF를 인덱싱하세요."
        )
        
    generated_questions = question_ai.generate_question_from_rag_chunks(
        subject=subject,
        chunks=chunks,
        question_type=question_type,
        difficulty=difficulty,
        count=count,
    )

    target_material_id = (
        material_id
        or chunks[0]["metadata"].get("material_id")
    )

    material = (
        db.query(models.StudyMaterial)
        .filter(models.StudyMaterial.id == target_material_id)
        .filter(models.StudyMaterial.user_id == user_id)
        .filter(models.StudyMaterial.subject == subject)
        .first()
    )

    if material is None:
        raise ResourceNotFoundError(
            "연결할 StudyMaterial을 찾지 못했습니다."
        )
    
    saved_questions = []
        
    try:
        for item in generated_questions:
            question = models.Question(
                material_id=material.id,
                question_text=item.get("question", ""),
                answer=item.get("answer", ""),
                explanation=item.get("explanation", ""),
                concept=item.get("concept", ""),
                question_type=question_type,
                difficulty=difficulty,
            )
            
            db.add(question)
            saved_questions.append(question)
            
        db.commit()
        
        for question in saved_questions:
            db.refresh(question)
            
    except Exception:
        db.rollback()
        raise
        
    return {
        "question_count": len(saved_questions),
        "material_id": target_material_id,
        "questions": saved_questions,
    }


def generate_weakness_rag_questions(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    subject: str,
    material_id: int | None = None,
    weakness_count: int = 3,
    question_count: int = 5,
    question_type: str = "short_answer",
    difficulty: str = "exam_like",
    top_k_per_concept: int = 3,
    
):
    weakness_rows = (
        db.query(
            models.WrongAnswer.concept,
            func.count(models.WrongAnswer.id).label("wrong_count"),
        )
        .filter(models.WrongAnswer.user_id == user_id)
        .filter(models.WrongAnswer.concept.isnot(None))
        .filter(models.WrongAnswer.concept != "")
        .group_by(models.WrongAnswer.concept)
        .order_by(func.count(models.WrongAnswer.id).desc())
        .limit(weakness_count)
        .all()
    )
    
    if not weakness_rows:
        raise ResourceNotFoundError(
            "오답 기록이 없습니다. 먼저 문제를 풀고 오답을 저장하세요."
        )
        
    weakness_concepts = [row.concept for row in weakness_rows]
    
    all_chunks = []
    seen_chunk_keys = set()
    
    for concept in weakness_concepts:
        chunks = rag_service.retrieve_chunks_by_concept(
            user_name=user_name,
            subject=subject,
            concept=concept,
            material_id=material_id,
            top_k=top_k_per_concept,
        )
        
        for chunk in chunks:
            metadata = chunk["metadata"]
            key = (
                metadata.get("material_id"),
                metadata.get("page_number"),
                metadata.get("chunk_index"),
            )
            
            if key not in seen_chunk_keys:
                seen_chunk_keys.add(key)
                all_chunks.append(chunk)
                
    if not all_chunks:
        raise ResourceNotFoundError(
            "약점 개념과 관련된 RAG 문서 chunk를 찾지 못했습니다."
        )
        
    generated_questions = question_ai.generate_weakness_questions_from_rag_chunks(
        subject=subject,
        weakness_concepts=weakness_concepts,
        chunks=all_chunks,
        question_type=question_type,
        difficulty=difficulty,
        count=question_count,
    )
    
    target_material_id = material_id or all_chunks[0]["metadata"].get("material_id")
    
    material = (
        db.query(models.StudyMaterial)
        .filter(models.StudyMaterial.id == target_material_id)
        .filter(
            models.StudyMaterial.user_id == user_id
        )
        .filter(models.StudyMaterial.subject == subject)
        .first()
    )
    
    if material is None:
        raise ResourceNotFoundError(
            "연결할 StudyMaterial을 찾지 못했습니다."
        )
        
    saved_questions = []
    
    try:
        for item in generated_questions:
            question = models.Question(
                material_id=material.id,
                question_text=item.get("question", ""),
                answer=item.get("answer", ""),
                explanation=item.get("explanation", ""),
                concept=item.get("concept", ""),
                question_type=question_type,
                difficulty=difficulty,
            )
            
            db.add(question)
            saved_questions.append(question)
            
        db.commit()
        
        for question in saved_questions:
            db.refresh(question)
            
    except Exception:
        db.rollback()
        raise
        
    return {
        "weakness_concepts": [
            {
                "concept": row.concept,
                "wrong_count": row.wrong_count,
            }
            for row in weakness_rows
        ],
        "used_chunk_count": len(all_chunks),
        "question_count": len(saved_questions),
        "material_id": target_material_id,
        "questions": saved_questions,
    }
