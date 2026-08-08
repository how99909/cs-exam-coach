from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import ai_service, models, schemas
from app.database import get_db

router = APIRouter(prefix="/exam-attempts", tags=["exam-attempts"])


@router.post("/submit")
def submit_exam_attempt(
    request: schemas.ExamAttemptSubmitRequest,
    db: Session = Depends(get_db),
): 
    if not request.answers:
        raise HTTPException(
            status_code=400,
            detail="제출할 답안이 없습니다.",
        )
        
    question_ids = [answer.question_id for answer in request.answers]
    
    questions = (
        db.query(models.Question)
        .join(models.StudyMaterial, models.Question.material_id == models.StudyMaterial.id)
        .filter(models.StudyMaterial.user_name == request.user_name)
        .filter(models.StudyMaterial.subject == request.subject)
        .filter(models.Question.id.in_(question_ids))
        .all()
    )
    
    question_map = {question.id: question for question in questions}
    
    if len(question_map) != len(set(question_ids)):
        raise HTTPException(
            status_code=404,
            detail="일부 문제를 찾지 못했습니다.",
        )
        
    attempt = models.ExamAttempt(
        user_name=request.user_name,
        subject=request.subject,
        title=request.title,
        total_questions=len(request.answers),
        correct_count=0,
        score=0,
    )
    
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    results = []
    correct_count = 0
    
    for answer_item in request.answers:
        question = question_map[answer_item.question_id]
        
        grading_result = ai_service.grade_exam_answer(
            question_text=question.question_text,
            correct_answer=question.answer,
            explanation=question.explanation,
            user_answer=answer_item.user_answer,
        )
        
        is_correct = grading_result["is_correct"]
        
        if is_correct:
            correct_count += 1
            
        attempt_answer = models.ExamAttemptAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            user_answer=answer_item.user_answer,
            is_correct=is_correct,
            feedback=grading_result["feedback"],
        )
        
        db.add(attempt_answer)
        
        if not is_correct:
            wrong_answer = models.WrongAnswer(
                user_name=request.user_name,
                question_id=question.id,
                user_answer=answer_item.user_answer,
                correct_answer=question.answer,
                explanation=question.explanation,
                concept=question.concept,
            )
            db.add(wrong_answer)
            
        results.append(
            {
                "question_id": question.id,
                "question": question.question_text,
                "user_answer": answer_item.user_answer,
                "correct_answer": question.answer,
                "is_correct": is_correct,
                "feedback": grading_result["feedback"],
                "concept": question.concept,
            }
        )
        
    score = round((correct_count / len(request.answers)) * 100)
    
    attempt.correct_count = correct_count
    attempt.score = score
    
    db.commit()
    db.refresh(attempt)
    
    return {
        "success": True,
        "message": "시험 응시 결과가 저장되었습니다.",
        "attempt_id": attempt.id,
        "title": attempt.title,
        "subject": attempt.subject,
        "total_questions": attempt.total_questions,
        "correct_count": attempt.correct_count,
        "score": attempt.score,
        "results": results,
    }
    
    
@router.get("/history")
def get_exam_attempt_history(
    user_name: str,
    subject: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(models.ExamAttempt).filter(
        models.ExamAttempt.user_name == user_name
    )
    
    if subject:
        query = query.filter(models.ExamAttempt.subject == subject)
        
    attempts = (
        query.order_by(models.ExamAttempt.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return {
        "success": True,
        "attempt_count": len(attempts),
        "attempts": [
            {
                "id": attempt.id,
                "subject": attempt.subject,
                "title": attempt.title,
                "total_questions": attempt.total_questions,
                "correct_count": attempt.correct_count,
                "score": attempt.score,
                "created_at": attempt.created_at,
            }
            for attempt in attempts
        ],
    }
    
    
@router.get("/{attempt_id}")
def get_exam_attempt_detail(
    attempt_id: int,
    user_name: str,
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(models.ExamAttempt)
        .filter(models.ExamAttempt.id == attempt_id)
        .filter(models.ExamAttempt.user_name == user_name)
        .first()
    )
    
    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="응시 기록을 찾지 못했습니다.",
        )
        
    answers = (
        db.query(models.ExamAttemptAnswer, models.Question)
        .join(models.Question, models.ExamAttemptAnswer.question_id == models.Question.id)
        .filter(models.ExamAttemptAnswer.attempt_id == attempt.id)
        .all()
    )
    
    return {
        "success": True,
        "attempt": {
            "id": attempt.id,
            "subject": attempt.subject,
            "title": attempt.title,
            "total_questions": attempt.total_questions,
            "correct_count": attempt.correct_count,
            "score": attempt.score,
            "created_at": attempt.created_at,
        },
        "answers": [
            {
                "question_id": question.id,
                "question": question.question_text,
                "user_answer": answer.user_answer,
                "correct_answer": question.answer,
                "is_correct": answer.is_correct,
                "feedback": answer.feedback,
                "concept": question.concept,
            }
            for answer, question in answers
        ],
    }
    
    
@router.get("/analytics")
def get_exam_attempt_analytics(
    user_name: str,
    subject: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    attempt_query = db.query(models.ExamAttempt).filter(
        models.ExamAttempt.user_name == user_name
    )
    
    if subject:
        attempt_query = attempt_query.filter(models.ExamAttempt.subject == subject)
        
    attempts = (
        attempt_query.order_by(models.ExamAttempt.created_at.desc())
        .limit(limit)
        .all()
    )
    
    if not attempts:
        return {
            "success": True,
            "message": "응시 기록이 없습니다.",
            "attempt_count": 0,
            "average_score": None,
            "latest_score": None,
            "score_trend": [],
            "weak_concepts": [],
            "subject_summary": [],
        }
        
    attempt_ids = [attempt.id for attempt in attempts]
    
    average_score = round(
        sum(attempt.score for attempt in attempts) / len(attempts),
        2,
    )
    
    latest_score = attempts[0].score
    
    score_trend = [
        {
            "attempt_id": attempt.id,
            "title": attempt.title,
            "subject": attempt.subject,
            "score": attempt.score,
            "correct_count": attempt.correct_count,
            "total_questions": attempt.total_questions,
            "created_at": attempt.created_at,
        }
        for attempt in reversed(attempts)
    ]
    
    wrong_rows = (
        db.query(
            models.Question.concept,
            func.count(models.ExamAttemptAnswer.id).label("wrong_count"),
        )
        .join(
            models.ExamAttemptAnswer,
            models.ExamAttemptAnswer.question_id == models.Question.id,
        )
        .filter(models.ExamAttemptAnswer.attempt_id.in_(attempt_ids))
        .filter(models.ExamAttemptAnswer.is_correct == False)
        .filter(models.Question.concept.isnot(None))
        .filter(models.Question.concept != "")
        .group_by(models.Question.concept)
        .order_by(func.count(models.ExamAttemptAnswer.id).desc())
        .limit(10)
        .all()
    )
    
    weak_concepts = [
        {
            "concept": row.concept,
            "wrong_count": row.wrong_count,
        }
        for row in wrong_rows
    ]
    
    subject_rows = (
        db.query(
            models.ExamAttempt.subject,
            func.count(models.ExamAttempt.id).label("attempt_count"),
            func.avg(models.ExamAttempt.score).label("avg_score"),
            func.max(models.ExamAttempt.score).label("max_score"),
            func.min(models.ExamAttempt.score).label("min_score"),
        )
        .filter(models.ExamAttempt.user_name == user_name)
        .group_by(models.ExamAttempt.subject)
        .all()
    )
    
    subject_summary = [
        {
            "subject": row.subject,
            "attempt_count": row.attempt_count,
            "avg_score": round(float(row.avg_score), 2),
            "max_score": row.max_score,
            "min_score": row.min_score,
        }
        for row in subject_rows
    ]
    
    return {
        "success": True,
        "attempt_count": len(attempts),
        "average_score": average_score,
        "latest_score": latest_score,
        "score_trend": score_trend,
        "weak_concepts": weak_concepts,
        "subject_summary": subject_summary,
    }