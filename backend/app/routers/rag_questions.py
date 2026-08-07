from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import ai_service, models, rag_service, schemas
from app.database import get_db

router = APIRouter(prefix="/rag-questions", tags=["rag-questions"])


@router.post("/generate")
def generate_rag_based_questions(
    request: schemas.RagQuestionGenerateRequest,
    db: Session = Depends(get_db),
):
    chunks = rag_service.get_document_chunks_for_question_generation(
        user_name=request.user_name,
        subject=request.subject,
        material_id=request.material_id,
        limit=request.top_k,
    )
    
    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="문제 생성을 위한 RAG 문서 chunk를 찾지 못했습니다. 먼저 PDF를 인덱싱하세요.",
        )
        
    generated_questions = ai_service.generate_question_from_rag_chunks(
        subject=request.subject,
        chunks=chunks,
        question_type=request.question_type,
        difficulty=request.difficulty,
        count=request.count,
    )
    
    saved_questions = []
    
    target_material_id = request.material_id or chunks[0]["metadata"].get("material_id")
    
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
        
    for item in generated_questions:
        question = models.Question(
            material_id=material.id,
            question_text=item.get("question", ""),
            answer=item.get("answer", ""),
            explanation=item.get("explanation", ""),
            concept_tag=item.get("concept", ""),
            question_type=request.question_type,
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
                "concept": question.concept_tag,
                "question_type": question.question_type,
                "difficulty": request.difficulty,
                "source": item.get("source"),
            }
        )
        
    return {
        "success": True,
        "message": "RAG 기반 예상문제가 생성되었습니다.",
        "question_count": len(saved_questions),
        "material_id": target_material_id,
        "questions": saved_questions,
    }