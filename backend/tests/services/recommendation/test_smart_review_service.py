from datetime import timedelta

import pytest

from app import models
from app.ai import recommendation_ai
from app.services.exceptions import InvalidAIResponseError, ResourceNotFoundError
from app.services.recommendation import smart_review_service
from app.time_utils import utc_now


def _create_session(db, user, *, subject="algorithms"):
    session = models.StudySession(
        user_id=user.id,
        subject=subject,
        duration_minutes=30,
        content="Review graphs",
        created_at=utc_now() - timedelta(minutes=1),
    )
    db.add(session)
    db.commit()
    return session


def _create_wrong_answer(db, user, *, subject, concept):
    material = models.StudyMaterial(
        user_id=user.id,
        subject=subject,
        content="Study material",
    )
    db.add(material)
    db.flush()
    question = models.Question(
        material_id=material.id,
        question_text="Question",
        answer="Answer",
        concept=concept,
        question_type="short_answer",
        difficulty="medium",
    )
    db.add(question)
    db.flush()
    wrong_answer = models.WrongAnswer(
        user_id=user.id,
        question_id=question.id,
        user_answer="Wrong",
        correct_answer="Answer",
        concept=concept,
    )
    db.add(wrong_answer)
    db.commit()
    return wrong_answer


@pytest.mark.parametrize(
    "generated_items",
    [
        "not a list",
        [],
        ["not a mapping"],
        [{"title": ""}],
        [{"title": "Review BFS", "reason": 1}],
        [{"title": "Review BFS", "estimated_minutes": 0}],
        [{"title": "Review BFS", "priority": True}],
    ],
)
def test_generate_queue_rejects_invalid_ai_output(
    db,
    user_a,
    monkeypatch,
    generated_items,
):
    _create_session(db, user_a)
    monkeypatch.setattr(
        recommendation_ai,
        "generate_smart_review_queue_items",
        lambda **kwargs: generated_items,
    )

    with pytest.raises(InvalidAIResponseError):
        smart_review_service.generate_and_save_queue(
            db=db,
            user_id=user_a.id,
            user_name=user_a.user_name,
            subject="algorithms",
            limit=5,
        )

    assert db.query(models.SmartReviewQueueItem).count() == 0


def test_generate_queue_filters_recent_wrong_answers_by_subject(
    db,
    user_a,
    monkeypatch,
):
    algorithms_wrong = _create_wrong_answer(
        db, user_a, subject="algorithms", concept="BFS"
    )
    _create_wrong_answer(db, user_a, subject="databases", concept="SQL")
    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return [{"title": "Review BFS", "priority": 1}]

    monkeypatch.setattr(
        recommendation_ai,
        "generate_smart_review_queue_items",
        fake_generate,
    )

    result = smart_review_service.generate_and_save_queue(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        subject="algorithms",
        limit=5,
    )

    assert [item["id"] for item in captured["recent_wrong_answers"]] == [
        algorithms_wrong.id
    ]
    assert result["item_count"] == 1
    assert result["items"][0].title == "Review BFS"


def test_update_queue_item_rejects_another_users_item(db, user_a, user_b):
    item = models.SmartReviewQueueItem(
        user_id=user_b.id,
        title="Private review",
        priority=1,
    )
    db.add(item)
    db.commit()

    with pytest.raises(ResourceNotFoundError):
        smart_review_service.update_queue_item(
            db=db,
            user_id=user_a.id,
            item_id=item.id,
            is_done=True,
        )


def test_update_queue_item_rolls_back_when_commit_fails(
    db,
    user_a,
    monkeypatch,
):
    item = models.SmartReviewQueueItem(
        user_id=user_a.id,
        title="Review BFS",
        priority=1,
    )
    db.add(item)
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
        smart_review_service.update_queue_item(
            db=db,
            user_id=user_a.id,
            item_id=item.id,
            is_done=True,
        )

    assert rollback_called is True
