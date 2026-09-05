from datetime import timedelta

import pytest

from app import models
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.services.feedback import rag_feedback_service
from app.time_utils import utc_now


def _create_material(db, user, *, subject="algorithms"):
    material = models.StudyMaterial(
        user_id=user.id,
        subject=subject,
        content="Study material",
    )
    db.add(material)
    db.flush()
    return material


def _add_feedback(
    db,
    user,
    *,
    subject="algorithms",
    accuracy=3,
    created_at=None,
):
    feedback = models.RagAnswerFeedback(
        user_id=user.id,
        subject=subject,
        question="Question",
        answer="Answer",
        accuracy_score=accuracy,
        grounding_score=4,
        source_relevance_score=2,
        helpfulness_score=5,
        created_at=created_at or utc_now(),
    )
    db.add(feedback)
    db.flush()
    return feedback


def test_create_feedback_saves_normalized_fields(db, user_a):
    material = _create_material(db, user_a)
    db.commit()

    result = rag_feedback_service.create_feedback(
        db=db,
        user_id=user_a.id,
        subject=" algorithms ",
        material_id=material.id,
        question=" Question? ",
        answer=" Answer. ",
        accuracy_score=5,
        grounding_score=4,
        source_relevance_score=3,
        helpfulness_score=2,
        comment="   ",
    )

    feedback = db.get(models.RagAnswerFeedback, result["feedback_id"])
    assert feedback.subject == "algorithms"
    assert feedback.question == "Question?"
    assert feedback.answer == "Answer."
    assert feedback.comment is None
    assert feedback.user_id == user_a.id


def test_create_feedback_rejects_other_users_or_mismatched_material(
    db,
    user_a,
    user_b,
):
    other_users = _create_material(db, user_b)
    wrong_subject = _create_material(db, user_a, subject="databases")
    db.commit()

    with pytest.raises(ResourceNotFoundError):
        rag_feedback_service.create_feedback(
            db=db, user_id=user_a.id, subject="algorithms",
            material_id=other_users.id, question="Q", answer="A",
            accuracy_score=3, grounding_score=3,
            source_relevance_score=3, helpfulness_score=3, comment=None,
        )

    with pytest.raises(InvalidRequestError):
        rag_feedback_service.create_feedback(
            db=db, user_id=user_a.id, subject="algorithms",
            material_id=wrong_subject.id, question="Q", answer="A",
            accuracy_score=3, grounding_score=3,
            source_relevance_score=3, helpfulness_score=3, comment=None,
        )


@pytest.mark.parametrize("score", [0, 6, True, 3.5, "3"])
def test_create_feedback_rejects_invalid_scores(db, user_a, score):
    with pytest.raises(InvalidRequestError):
        rag_feedback_service.create_feedback(
            db=db, user_id=user_a.id, subject="algorithms",
            material_id=None, question="Q", answer="A",
            accuracy_score=score, grounding_score=3,
            source_relevance_score=3, helpfulness_score=3, comment=None,
        )


def test_summary_and_recent_are_user_and_subject_scoped(db, user_a, user_b):
    now = utc_now()
    older = _add_feedback(
        db, user_a, accuracy=1, created_at=now - timedelta(minutes=2)
    )
    newer = _add_feedback(
        db, user_a, accuracy=3, created_at=now - timedelta(minutes=1)
    )
    _add_feedback(db, user_a, subject="databases", accuracy=5)
    _add_feedback(db, user_b, accuracy=5)
    db.commit()

    summary = rag_feedback_service.get_summary(
        db=db,
        user_id=user_a.id,
        subject=" algorithms ",
    )
    assert summary["feedback_count"] == 2
    assert summary["avg_accuracy_score"] == 2.0

    recent = rag_feedback_service.get_recent(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        subject="algorithms",
        limit=1,
    )
    assert len(recent) == 1
    assert recent[0]["id"] == newer.id
    assert recent[0]["id"] != older.id
    assert recent[0]["user_name"] == user_a.user_name


def test_empty_summary_returns_message(db, user_a):
    result = rag_feedback_service.get_summary(
        db=db,
        user_id=user_a.id,
        subject=None,
    )

    assert result["feedback_count"] == 0
    assert "message" in result


def test_create_feedback_rolls_back_when_commit_fails(
    db,
    user_a,
    monkeypatch,
):
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
        rag_feedback_service.create_feedback(
            db=db, user_id=user_a.id, subject="algorithms",
            material_id=None, question="Q", answer="A",
            accuracy_score=3, grounding_score=3,
            source_relevance_score=3, helpfulness_score=3, comment=None,
        )

    assert rollback_called is True
