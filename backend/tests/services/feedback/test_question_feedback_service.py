from datetime import timedelta

import pytest

from app import models
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.services.feedback import question_feedback_service
from app.time_utils import utc_now


def _create_question(db, user):
    material = models.StudyMaterial(
        user_id=user.id,
        subject="algorithms",
        content="Graphs",
    )
    db.add(material)
    db.flush()
    question = models.Question(
        material_id=material.id,
        question_text="What is BFS?",
        answer="Breadth-first search",
        question_type="short_answer",
        difficulty="medium",
    )
    db.add(question)
    db.flush()
    return question


def _add_feedback(
    db,
    user,
    question,
    *,
    quality=3,
    relevance=3,
    comment=None,
    created_at=None,
):
    feedback = models.QuestionFeedback(
        user_id=user.id,
        question_id=question.id,
        quality_score=quality,
        explanation_score=4,
        exam_relevance_score=relevance,
        difficulty_match_score=2,
        comment=comment,
        created_at=created_at or utc_now(),
    )
    db.add(feedback)
    db.flush()
    return feedback


def test_create_feedback_checks_ownership_and_normalizes_comment(
    db,
    user_a,
    user_b,
):
    own_question = _create_question(db, user_a)
    other_question = _create_question(db, user_b)
    db.commit()

    result = question_feedback_service.create_feedback(
        db=db,
        user_id=user_a.id,
        question_id=own_question.id,
        quality_score=5,
        explanation_score=4,
        exam_relevance_score=3,
        difficulty_match_score=2,
        comment="   ",
    )

    feedback = db.get(models.QuestionFeedback, result["feedback_id"])
    assert feedback.comment is None

    with pytest.raises(ResourceNotFoundError):
        question_feedback_service.create_feedback(
            db=db,
            user_id=user_a.id,
            question_id=other_question.id,
            quality_score=5,
            explanation_score=4,
            exam_relevance_score=3,
            difficulty_match_score=2,
            comment=None,
        )


@pytest.mark.parametrize("score", [0, 6, True, 3.5, "3"])
def test_create_feedback_rejects_invalid_scores(db, user_a, score):
    question = _create_question(db, user_a)
    db.commit()

    with pytest.raises(InvalidRequestError):
        question_feedback_service.create_feedback(
            db=db,
            user_id=user_a.id,
            question_id=question.id,
            quality_score=score,
            explanation_score=3,
            exam_relevance_score=3,
            difficulty_match_score=3,
            comment=None,
        )


def test_empty_summary_does_not_convert_null_averages(db, user_a):
    assert question_feedback_service.get_summary(
        db=db,
        user_id=user_a.id,
    ) == {
        "feedback_count": 0,
        "message": "아직 평가가 없습니다.",
    }


def test_summaries_and_dashboard_are_user_scoped(
    db,
    user_a,
    user_b,
):
    question = _create_question(db, user_a)
    other_question = _create_question(db, user_b)
    now = utc_now()
    _add_feedback(
        db, user_a, question, quality=1, relevance=2,
        comment="Older", created_at=now - timedelta(minutes=2),
    )
    _add_feedback(
        db, user_a, question, quality=3, relevance=4,
        comment="Newer", created_at=now - timedelta(minutes=1),
    )
    _add_feedback(db, user_b, other_question, quality=5, relevance=5)
    db.commit()

    summary = question_feedback_service.get_summary(db=db, user_id=user_a.id)
    assert summary["feedback_count"] == 2
    assert summary["avg_quality_score"] == 2.0

    question_summary = question_feedback_service.get_question_summary(
        db=db,
        user_id=user_a.id,
        question_id=question.id,
    )
    assert question_summary["recent_comments"] == ["Newer", "Older"]

    dashboard = question_feedback_service.get_admin_dashboard(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
    )
    assert dashboard["feedback_count"] == 2
    assert dashboard["recent_comments"][0]["user_name"] == user_a.user_name
    assert dashboard["low_score_questions"][0]["question_id"] == question.id


@pytest.mark.parametrize("threshold", [0, 6, float("nan"), float("inf"), True])
def test_low_score_queries_reject_invalid_thresholds(db, user_a, threshold):
    with pytest.raises(InvalidRequestError):
        question_feedback_service.get_low_score_questions(
            db=db,
            user_id=user_a.id,
            threshold=threshold,
        )


def test_create_feedback_rolls_back_when_commit_fails(
    db,
    user_a,
    monkeypatch,
):
    question = _create_question(db, user_a)
    db.commit()
    original_rollback = db.rollback
    rollback_called = False

    def fail_commit():
        raise RuntimeError("commit failed")

    def track_rollback():
        nonlocal rollback_called
        rollback_called = True
        original_rollback()

    monkeypatch.setattr(db, "commit", fail_commit)
    monkeypatch.setattr(db, "rollback", track_rollback)

    with pytest.raises(RuntimeError, match="commit failed"):
        question_feedback_service.create_feedback(
            db=db,
            user_id=user_a.id,
            question_id=question.id,
            quality_score=3,
            explanation_score=3,
            exam_relevance_score=3,
            difficulty_match_score=3,
            comment=None,
        )

    assert rollback_called is True
