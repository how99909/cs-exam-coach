from datetime import date, timedelta

import pytest

from app import models
from app.services import review_service
from app.services.exceptions import InvalidRequestError


def _add_wrong_answer(
    db,
    user,
    *,
    concept,
    is_correct=False,
):
    db.add(
        models.WrongAnswer(
            user_id=user.id,
            question_id=1,
            user_answer="Wrong",
            correct_answer="Answer",
            concept=concept,
            is_correct=is_correct,
        )
    )


def test_weak_concepts_filters_user_and_correct_answers_and_keeps_contract(
    db,
    user_a,
    user_b,
):
    _add_wrong_answer(db, user_a, concept="BFS")
    _add_wrong_answer(db, user_a, concept="BFS")
    _add_wrong_answer(db, user_a, concept=None)
    _add_wrong_answer(db, user_a, concept="DFS", is_correct=True)
    _add_wrong_answer(db, user_b, concept="SQL")
    db.commit()

    assert review_service.get_weak_concepts(
        db=db,
        user_id=user_a.id,
    ) == [
        {
            "concept": "BFS",
            "wrong_count": 2,
            "recommendation": "BFS 개념을 우선 복습하세요.",
        },
        {
            "concept": "미분류",
            "wrong_count": 1,
            "recommendation": "미분류 개념을 우선 복습하세요.",
        },
    ]


@pytest.mark.parametrize("exam_date", [None, "", "2026/08/01", "not-a-date"])
def test_study_plan_rejects_missing_or_invalid_exam_date(
    db,
    user_a,
    exam_date,
):
    with pytest.raises(InvalidRequestError):
        review_service.get_study_plan(
            db=db,
            user_id=user_a.id,
            user_name=user_a.user_name,
            exam_date=exam_date,
        )


def test_study_plan_rejects_past_date(db, user_a):
    with pytest.raises(InvalidRequestError):
        review_service.get_study_plan(
            db=db,
            user_id=user_a.id,
            user_name=user_a.user_name,
            exam_date=(date.today() - timedelta(days=1)).isoformat(),
        )


@pytest.mark.parametrize("days_left", [0, 1, 2, 3, 7, 8])
def test_study_plan_has_unique_non_reversed_day_ranges(
    db,
    user_a,
    days_left,
):
    for concept in ["BFS", "DFS", "Tree", "Sort", "Heap", "Graph"]:
        _add_wrong_answer(db, user_a, concept=concept)
    db.commit()

    result = review_service.get_study_plan(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        exam_date=(date.today() + timedelta(days=days_left)).isoformat(),
    )

    labels = [item["day"] for item in result["plan"]]
    assert result["success"] is True
    assert result["days_left"] == days_left
    assert len(labels) == len(set(labels))
    assert "D-1 ~ D-2" not in labels


def test_study_plan_without_wrong_answers_returns_empty_successful_plan(
    db,
    user_a,
):
    result = review_service.get_study_plan(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        exam_date=(date.today() + timedelta(days=7)).isoformat(),
    )

    assert result["success"] is True
    assert result["plan"] == []
    assert "message" in result
