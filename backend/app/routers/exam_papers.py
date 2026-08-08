from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/exam-papers", tags=["exam-papers"])


@router.get("/questions")
def list_questions_for_exam_paper(
    user_name: str,
    subject: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    questions = (
        db.query(models.Question)
        .join(models.StudyMaterial, models.Question.material_id == models.StudyMaterial.id)
        .filter(models.StudyMaterial.user_name == user_name)
        .filter(models.StudyMaterial.subject == subject)
        .order_by(models.Question.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return {
        "success": True,
        "question_count": len(questions),
        "questions": [
            {
                "id": question.id,
                "question": question.question_text,
                "answer": question.answer,
                "explanation": question.explanation,
                "concept": question.concept,
                "question_type": question.question_type,
                "difficulty": question.difficulty,
                "created_at": question.created_at
            }
            for question in questions
        ],
    }
    
    
@router.post("/generate")
def generate_exam_paper(
    request: schemas.ExamPaperGenerateRequest,
    db: Session = Depends(get_db),
):
    if not request.question_ids:
        raise HTTPException(
            status_code=400,
            detail="시험지에 포함할 question_ids가 필요합니다.",
        )
        
    questions = (
        db.query(models.Question)
        .join(models.StudyMaterial, models.Question.material_id == models.StudyMaterial.id)
        .filter(models.StudyMaterial.user_name == request.user_name)
        .filter(models.StudyMaterial.subject == request.subject)
        .filter(models.Question.id.in_(request.question_ids))
        .all()
    )
    
    if not questions:
        raise HTTPException(
            status_code=404,
            detail="선택한 문제를 찾지 못했습니다.",
        )

    found_question_ids = {question.id for question in questions}
    missing_question_ids = sorted(set(request.question_ids) - found_question_ids)

    if missing_question_ids:
        raise HTTPException(
            status_code=404,
            detail=f"접근할 수 없는 question_ids: {missing_question_ids}",
        )
        
    question_order = {question_id: index for index, question_id in enumerate(request.question_ids)}
    questions.sort(key=lambda question: question_order.get(question.id, 999999))
    
    paper_lines = []
    
    paper_lines.append(f"# {request.title}")
    paper_lines.append("")
    paper_lines.append(f"- 사용자: {request.user_name}")
    paper_lines.append(f"- 과목: {request.subject}")
    paper_lines.append(f"- 문항 수: {len(questions)}")
    paper_lines.append("")
    paper_lines.append("---")
    paper_lines.append("")
    
    for index, question in enumerate(questions, start=1):
        paper_lines.append(f"## 문제 {index}")
        paper_lines.append("")
        paper_lines.append(f"**유형:** {question.question_type}")
        paper_lines.append(f"**난이도:** {question.difficulty}")
        paper_lines.append(f"**개념:** {question.concept}")
        paper_lines.append("")
        paper_lines.append(question.question_text)
        paper_lines.append("")
        
        if request.include_answers:
            paper_lines.append("### 정답")
            paper_lines.append("")
            paper_lines.append(question.answer)
            paper_lines.append("")
            
        if request.include_explanations:
            paper_lines.append("### 해설")
            paper_lines.append("")
            paper_lines.append(question.explanation or "")
            paper_lines.append("")
            
        paper_lines.append("---")
        paper_lines.append("")
        
    markdown = "\n".join(paper_lines)
    
    return {
        "success": True,
        "message": "시험지가 생성되었습니다.",
        "title": request.title,
        "question_count": len(questions),
        "include_answers": request.include_answers,
        "include_explanations": request.include_explanations,
        "markdown": markdown,
    }
