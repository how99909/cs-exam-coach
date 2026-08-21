from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date

from app import models
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/recommendations")
def get_review_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user_name = current_user.user_name
    
    results = (
        db.query(
            models.WrongAnswer.concept,
            func.count(models.WrongAnswer.id).label("wrong_count")
        )
        .filter(models.WrongAnswer.user_name == user_name)
        .filter(models.WrongAnswer.is_correct == False)
        .group_by(models.WrongAnswer.concept)
        .order_by(func.count(models.WrongAnswer.id).desc())
        .all()
    )
    
    return [
        {
            "concept": concept or "미분류",
            "wrong_count": wrong_count,
            "recommendation": f"{concept or '미분류'} 개념을 우선 복습하세요."
        }
        for concept, wrong_count in results
    ]
    
@router.get("/study-plan")
def get_study_plan(
    exam_date: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user_name = current_user.user_name
    
    if exam_date is None:
        return {
            "success": False,
            "message": "exam_date를 YYYY-MM-DD 형식으로 입력하세요.",
        }
    
    try:
        target_date = datetime.strptime(exam_date, "%Y-%m-%d").date()
    except ValueError:
        return {
            "success": False,
            "message": "exam_date 형식이 올바르지 않습니다. 예: 2026-08-01",
        }
        
    today = date.today()
    days_left = (target_date - today).days
    
    if days_left < 0:
        return {
            "success": False,
            "message": "시험 날짜는 현재 날짜보다 나중이어야 합니다.",
        }
        
    results = (
        db.query(
            models.WrongAnswer.concept,
            func.count(models.WrongAnswer.id).label("wrong_count")
        )
        .filter(models.WrongAnswer.user_name == user_name)
        .filter(models.WrongAnswer.is_correct == False)
        .group_by(models.WrongAnswer.concept)
        .order_by(func.count(models.WrongAnswer.id).desc())
        .all()
    )
    
    weak_concepts = [
        {
            "concept": concept or "미분류",
            "wrong_count": wrong_count,
        }
        for concept, wrong_count in results
    ]
    
    if not weak_concepts:
        return {
            "success": True,
            "user_name": user_name,
            "exam_date": exam_date,
            "days_left": days_left,
            "message": "아직 오답 기록이 없습니다. 먼저 문제를 풀고 오답을 기록하세요.",
            "plan": [],
        }
        
    plan = []
    
    if days_left == 0:
        plan.append(
            {
                "day": "D-Day",
                "task": "새로운 개념보다 기존 오답 개념과 핵심 요약을 빠르게 복습하세요.",
                "concepts": [item["concept"] for item in weak_concepts[:5]],
            }
        )
        
    elif days_left <= 2:
        plan.append(
            {
                "day": f"D-{days_left}",
                "task": "오답 빈도가 높은 개념을 우선 복습하고, 틀린 문제를 다시 풀어보세요.",
                "concepts": [item["concept"] for item in weak_concepts[:5]],
            }
        )
        plan.append(
            {
                "day": "D-1",
                "task": "새 문제보다 핵심 개념과 오답 노트를 중심으로 정리하세요.",
                "concepts": [item["concept"] for item in weak_concepts[:3]],
            }
        )
        
    elif days_left <= 7:
        midpoint = max(1, days_left // 2)
        
        plan.append(
            {
                "day": f"D-{days_left} ~ D-{midpoint + 1}",
                "task": "오답 빈도가 높은 약점 개념을 집중 복습하세요.",
                "concepts": [item["concept"] for item in weak_concepts[:3]],
            }
        )
        plan.append(
            {
                "day": f"D-{midpoint} ~ D-2",
                "task": "중간 우선순위 개념을 복습하고 관련 문제를 다시 풀어보세요.",
                "concepts": [item["concept"] for item in weak_concepts[3:6]],
            }
        )
        plan.append(
            {
                "day": "D-1",
                "task": "전체 오답 개념을 빠르게 훑고, 가장 많이 틀린 개념을 마지막으로 점검하세요.",
                "concepts": [item["concept"] for item in weak_concepts[:5]],
            }
        )
        
    else:
        plan.append(
            {
                "day": f"D-{days_left} ~ D-8",
                "task": "오답 빈도가 높은 개념부터 차근차근 복습하고, 관련 개념을 다시 정리하세요.",
                "concepts": [item["concept"] for item in weak_concepts[:3]],
            }
        )
        plan.append(
            {
                "day": "D-7 ~ D-4",
                "task": "중간 우선순위 개념을 복습하고 예상문제를 추가로 생성해 풀어보세요.",
                "concepts": [item["concept"] for item in weak_concepts[3:6]],
            }
        )
        plan.append(
            {
                "day": f"D-3 ~ D-2",
                "task": "오답 문제를 다시 풀고 채점 피드백을 확인하세요..",
                "concepts": [item["concept"] for item in weak_concepts[:5]],
            }
        )
        plan.append(
            {
                "day": "D-1",
                "task": "새로운 문제보다 핵심 요약, 오답 개념, 자주 틀린 개념을 최종 점검하세요.",
                "concepts": [item["concept"] for item in weak_concepts[:5]],
            }
        )
        
    return {
        "success": True,
        "user_name": user_name,
        "exam_date": exam_date,
        "days_left": days_left,
        "weak_concepts": weak_concepts,
        "plan": plan,
    }
