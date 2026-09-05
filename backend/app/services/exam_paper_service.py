from sqlalchemy.orm import Session

from app import models
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError


def list_questions(
    db: Session,
    *,
    user_id: int,
    subject: str,
    limit: int,
) -> dict:
    subject = subject.strip()
    if not subject:
        raise InvalidRequestError("과목을 입력해야 합니다.")
    if not 1 <= limit <= 100:
        raise InvalidRequestError("limit은 1 이상 100 이하이어야 합니다.")

    questions = (
        db.query(models.Question)
        .join(
            models.StudyMaterial, 
            models.Question.material_id == models.StudyMaterial.id
        )
        .filter(models.StudyMaterial.user_id == user_id)
        .filter(models.StudyMaterial.subject == subject)
        .order_by(models.Question.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return {
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
                "created_at": question.created_at,
            }
            for question in questions
        ],
    }
    

def generate_exam_paper(
    db: Session,
    *,
    user_id: int,
    user_name: str,
    subject: str,
    title: str,
    question_ids: list[int],
    include_answers: bool,
    include_explanations: bool,
) -> dict:
    subject = subject.strip()
    title = title.strip()

    if not subject:
        raise InvalidRequestError("과목을 입력해야 합니다.")
    if not title:
        raise InvalidRequestError("시험지 제목을 입력해야 합니다.")
    if not question_ids:
        raise InvalidRequestError(
            "시험지에 포함할 question_ids가 필요합니다."
        )

    if any(
        isinstance(question_id, bool)
        or not isinstance(question_id, int)
        or question_id <= 0
        for question_id in question_ids
    ):
        raise InvalidRequestError(
            "question_ids에는 양의 정수만 입력할 수 있습니다."
        )

    if len(question_ids) != len(set(question_ids)):
        raise InvalidRequestError(
            "question_ids에는 중복된 문제 ID를 포함할 수 없습니다."
        )
        
    questions = (
        db.query(models.Question)
        .join(
            models.StudyMaterial, 
            models.Question.material_id == models.StudyMaterial.id
        )
        .filter(models.StudyMaterial.user_id == user_id)
        .filter(models.StudyMaterial.subject == subject)
        .filter(models.Question.id.in_(question_ids))
        .all()
    )
    
    if not questions:
        raise ResourceNotFoundError(
            "선택한 문제를 찾지 못했습니다."
        )

    found_ids = {question.id for question in questions}
    missing_ids = sorted(set(question_ids) - found_ids)

    if missing_ids:
        raise ResourceNotFoundError(
            f"접근할 수 없는 question_ids: {missing_ids}"
        )
        
    order = {
        question_id: index 
        for index, question_id in enumerate(question_ids)
    }
    
    questions.sort(
        key=lambda question: 
        order.get(question.id, 999999)
    )
    
    paper_lines = []
    
    paper_lines.append(f"# {title}")
    paper_lines.append("")
    paper_lines.append(f"- 사용자: {user_name}")
    paper_lines.append(f"- 과목: {subject}")
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
        
        if include_answers:
            paper_lines.append("### 정답")
            paper_lines.append("")
            paper_lines.append(question.answer)
            paper_lines.append("")
            
        if include_explanations:
            paper_lines.append("### 해설")
            paper_lines.append("")
            paper_lines.append(question.explanation or "")
            paper_lines.append("")
            
        paper_lines.append("---")
        paper_lines.append("")
        
    markdown = "\n".join(paper_lines)
    
    return {
        "title": title,
        "question_count": len(questions),
        "include_answers": include_answers,
        "include_explanations": include_explanations,
        "markdown": markdown,
    }
