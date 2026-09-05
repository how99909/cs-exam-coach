from datetime import timedelta

import pytest

from app import models
from app.services import exam_paper_service
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.time_utils import utc_now


def _create_question(
    db,
    user,
    *,
    subject="algorithms",
    text="Question",
    created_at=None,
):
    material = models.StudyMaterial(
        user_id=user.id,
        subject=subject,
        content="Study material",
    )
    db.add(material)
    db.flush()
    question = models.Question(
        material_id=material.id,
        question_text=text,
        answer=f"Answer for {text}",
        explanation=f"Explanation for {text}",
        concept="BFS",
        question_type="short_answer",
        difficulty="medium",
        created_at=created_at or utc_now(),
    )
    db.add(question)
    db.flush()
    return question


def test_list_questions_filters_user_subject_orders_and_limits(
    db,
    user_a,
    user_b,
):
    now = utc_now()
    older = _create_question(
        db, user_a, text="Older", created_at=now - timedelta(minutes=2)
    )
    newer = _create_question(
        db, user_a, text="Newer", created_at=now - timedelta(minutes=1)
    )
    _create_question(db, user_a, subject="databases", text="Other subject")
    _create_question(db, user_b, text="Other user")
    db.commit()

    result = exam_paper_service.list_questions(
        db=db,
        user_id=user_a.id,
        subject=" algorithms ",
        limit=1,
    )

    assert result["question_count"] == 1
    assert result["questions"][0]["id"] == newer.id
    assert result["questions"][0]["question"] == "Newer"
    assert result["questions"][0]["id"] != older.id


def test_generate_exam_paper_preserves_requested_order_and_flags(
    db,
    user_a,
):
    first = _create_question(db, user_a, text="First question")
    second = _create_question(db, user_a, text="Second question")
    db.commit()

    result = exam_paper_service.generate_exam_paper(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        subject=" algorithms ",
        title=" Practice Exam ",
        question_ids=[second.id, first.id],
        include_answers=True,
        include_explanations=False,
    )

    assert result["title"] == "Practice Exam"
    assert result["question_count"] == 2
    assert result["include_answers"] is True
    assert result["include_explanations"] is False
    assert result["markdown"].index("Second question") < result["markdown"].index(
        "First question"
    )
    assert "Answer for Second question" in result["markdown"]
    assert "Explanation for Second question" not in result["markdown"]


def test_generate_exam_paper_rejects_inaccessible_or_wrong_subject_questions(
    db,
    user_a,
    user_b,
):
    own = _create_question(db, user_a)
    other_users = _create_question(db, user_b)
    other_subject = _create_question(db, user_a, subject="databases")
    db.commit()

    for question_id in [other_users.id, other_subject.id]:
        with pytest.raises(ResourceNotFoundError):
            exam_paper_service.generate_exam_paper(
                db=db,
                user_id=user_a.id,
                user_name=user_a.user_name,
                subject="algorithms",
                title="Exam",
                question_ids=[own.id, question_id],
                include_answers=False,
                include_explanations=False,
            )


@pytest.mark.parametrize(
    "question_ids",
    [[], [1, 1], [0], [-1], [True]],
)
def test_generate_exam_paper_rejects_invalid_question_ids(
    db,
    user_a,
    question_ids,
):
    with pytest.raises(InvalidRequestError):
        exam_paper_service.generate_exam_paper(
            db=db,
            user_id=user_a.id,
            user_name=user_a.user_name,
            subject="algorithms",
            title="Exam",
            question_ids=question_ids,
            include_answers=False,
            include_explanations=False,
        )


@pytest.mark.parametrize(
    ("subject", "title"),
    [("   ", "Exam"), ("algorithms", "   ")],
)
def test_generate_exam_paper_rejects_blank_text_fields(
    db,
    user_a,
    subject,
    title,
):
    with pytest.raises(InvalidRequestError):
        exam_paper_service.generate_exam_paper(
            db=db,
            user_id=user_a.id,
            user_name=user_a.user_name,
            subject=subject,
            title=title,
            question_ids=[1],
            include_answers=False,
            include_explanations=False,
        )


@pytest.mark.parametrize(
    ("subject", "limit"),
    [("   ", 10), ("algorithms", 0), ("algorithms", 101)],
)
def test_list_questions_rejects_invalid_filters(db, user_a, subject, limit):
    with pytest.raises(InvalidRequestError):
        exam_paper_service.list_questions(
            db=db,
            user_id=user_a.id,
            subject=subject,
            limit=limit,
        )
