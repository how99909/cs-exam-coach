from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from app.ai import grading_ai
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError


def submit_exam_attempt(
    db: Session,
    *,
    user_id: int,
    subject: str,
    title: str,
    answers: list[tuple[int, str]],
) -> tuple[
    models.ExamAttempt,
    list[dict[str, Any]],
]: 
    if not answers:
        raise InvalidRequestError(
            "제출할 답안이 없습니다."
        )
        
    question_ids = [question_id for question_id, _ in answers]

    if len(question_ids) != len(set(question_ids)):
        raise InvalidRequestError(
            "같은 문제의 답안을 중복 제출할 수 없습니다."
        )
    
    questions = (
        db.query(models.Question)
        .join(models.StudyMaterial, models.Question.material_id == models.StudyMaterial.id)
        .filter(models.StudyMaterial.user_id == user_id)
        .filter(models.StudyMaterial.subject == subject)
        .filter(models.Question.id.in_(question_ids))
        .all()
    )
    
    question_map = {question.id: question for question in questions}
    
    if len(question_map) != len(set(question_ids)):
        raise ResourceNotFoundError(
            "일부 문제를 찾지 못했습니다."
        )
        
    results = []
    correct_count = 0
    graded_answers = []
    
    for question_id, user_answer in answers:
        question = question_map[question_id]
        
        grading_result = grading_ai.grade_exam_answer(
            question_text=question.question_text,
            correct_answer=question.answer,
            explanation=question.explanation,
            user_answer=user_answer,
        )
        
        is_correct = grading_result["is_correct"]
        
        if is_correct:
            correct_count += 1
            
        graded_answers.append(
            (
                question,
                user_answer,
                grading_result,
            )
        )
            
        results.append(
            {
                "question_id": question.id,
                "question": question.question_text,
                "user_answer": user_answer,
                "correct_answer": question.answer,
                "is_correct": is_correct,
                "feedback": grading_result["feedback"],
                "concept": question.concept,
            }
        )
        
    score = round((correct_count / len(answers)) * 100)
    
    try:
        attempt = models.ExamAttempt(
            user_id=user_id,
            subject=subject,
            title=title,
            total_questions=len(answers),
            correct_count=correct_count,
            score=score,
        )
        db.add(attempt)
        db.flush()

        for question, user_answer, grading_result in graded_answers:
            is_correct = grading_result["is_correct"]
            db.add(
                models.ExamAttemptAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    user_answer=user_answer,
                    is_correct=is_correct,
                    feedback=grading_result["feedback"],
                )
            )

            if not is_correct:
                db.add(
                    models.WrongAnswer(
                        user_id=user_id,
                        question_id=question.id,
                        user_answer=user_answer,
                        correct_answer=question.answer,
                        concept=question.concept,
                        feedback=grading_result["feedback"],
                    )
                )

        db.commit()
        db.refresh(attempt)
        
    except Exception:
        db.rollback()
        raise
    
    return attempt, results


def get_exam_attempt_history(
    db: Session,
    *,
    user_id: int,
    subject: str | None = None,
    limit: int = 20,
) -> list[models.ExamAttempt]:
    query = db.query(models.ExamAttempt).filter(
        models.ExamAttempt.user_id == user_id
    )
    
    if subject:
        query = query.filter(models.ExamAttempt.subject == subject)
    
    return (
        query
        .order_by(models.ExamAttempt.created_at.desc())
        .limit(limit)
        .all()
    )
    
    
def get_exam_attempt_detail(
    db: Session,
    *,
    user_id: int,
    attempt_id: int,
):
    attempt = (
        db.query(models.ExamAttempt)
        .filter(models.ExamAttempt.id == attempt_id)
        .filter(models.ExamAttempt.user_id == user_id)
        .first()
    )
    
    if attempt is None:
        raise ResourceNotFoundError(
            "응시 기록을 찾지 못했습니다."
        )
        
    answers = (
        db.query(models.ExamAttemptAnswer, models.Question)
        .join(models.Question, models.ExamAttemptAnswer.question_id == models.Question.id)
        .filter(models.ExamAttemptAnswer.attempt_id == attempt.id)
        .all()
    )
    
    return attempt, answers


def get_exam_attempt_analytics(
    db: Session,
    *,
    user_id: int,
    subject: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    attempt_query = db.query(models.ExamAttempt).filter(
        models.ExamAttempt.user_id == user_id
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
        .filter(models.ExamAttempt.user_id == user_id)
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
        "attempt_count": len(attempts),
        "average_score": average_score,
        "latest_score": latest_score,
        "score_trend": score_trend,
        "weak_concepts": weak_concepts,
        "subject_summary": subject_summary,
    }
