from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import ai_service, models, rag_service, schemas
from app.database import get_db

router = APIRouter(
    prefix="/weakness-rag-questions",
    tags=["weakness-rag-questions"],
)

@router.post("/generate")
def generate_weakness_rag_questions(
    request: schemas.WeaknessRagQuestionRequest,
    db: Session = Depends(get_db),
):
    weakness_rows = (
        db.query(
            models.WrongAnswer.concept,
            func.count(models.WrongAnswer.id).label("wrong_count"),
        )
        .filter(models.WrongAnswer.user_name == request.user_name)
        .filter(models.WrongAnswer.concept.isnot(None))
        .filter(models.WrongAnswer.concept != "")
        .group_by(models.WrongAnswer.concept)
        .order_by(func.count(models.WrongAnswer.id).desc())
        .limit(request.weakness_count)
        .all()
    )
    
    if not weakness_rows:
        raise HTTPException(
            status_code=404,
            detail="오답 기록이 없습니다. 먼저 문제를 풀고 오답을 저장하세요.",
        )
        
    weakness_concepts = [row.concept for row in weakness_rows]
    
    all_chunks = []
    seen_chunk_keys = set()
    
    for concept in weakness_concepts:
        chunks = rag_service.retrieve_chunks_by_concept(
            user_name=request.user_name,
            subject=request.subject,
            concept=concept,
            material_id=request.material_id,
            top_k=request.top_k_per_concept,
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
        raise HTTPException(
            status_code=404,
            detail="약점 개념과 관련된 RAG 문서 chunk를 찾지 못했습니다.",
        )
        
    generated_questions = ai_service.generate_weakness_questions_from_rag_chunks(
        subject=request.subject,
        weakness_concepts=weakness_concepts,
        chunks=all_chunks,
        question_type=request.question_type,
        difficulty=request.difficulty,
        count=request.question_count,
    )
    
    target_material_id = request.material_id or all_chunks[0]["metadata"].get("material_id")
    
    material = (
        db.query(models.StudyMaterial)
        .filter(models.StudyMaterial.id == target_material_id)
        .first()
    )
    
    if material is None:
        raise HTTPException(
            status_code=404,
            detail="연결할 StudyMaterial을 찾지 못했습니다.",
        )
        
    saved_questions = []
    
    for item in generated_questions:
        question = models.Question(
            material_id=material.id,
            question_text=item.get("question", ""),
            answer=item.get("answer", ""),
            explanation=item.get("explanation", ""),
            concept=item.get("concept", ""),
            question_type=request.question_type,
            difficulty=request.difficulty,
        )
        
        db.add(question)
        db.commit()
        db.refresh(question)
        
        saved_questions.append(
            {
                "id": question.id,
                "question": question.question_text,
                "answer": question.answer,
                "explanation": question.explanation,
                "concept": question.concept,
                "question_type": question.question_type,
                "difficulty": question.difficulty,
                "source": item.get("source"),
            }
        )
        
    return {
        "success": True,
        "message": "약점 기반 RAG 복습 문제가 생성되었습니다.",
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
