from datetime import date, timedelta

import pytest

from app import models
from app.ai import study_ai
from app.services.exceptions import InvalidRequestError, ResourceNotFoundError
from app.services.study import checklist_service


def _create_goal(db, user):
    goal = models.StudyGoal(
        user_id=user.id,
        subject="algorithms",
        title="Algorithm exam",
        target_score=90,
        exam_date=date.today() + timedelta(days=7),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def test_generate_checklist_saves_generated_items(db, user_a, monkeypatch):
    goal = _create_goal(db, user_a)
    status = {
        "goal": {"id": goal.id, "subject": goal.subject},
        "current_status": {"target_score": 90},
        "weak_concepts": [{"concept": "BFS", "wrong_count": 2}],
    }
    captured = {}
    monkeypatch.setattr(
        checklist_service.goal_service,
        "get_goal_status",
        lambda **kwargs: status,
    )

    def fake_generate_items(**kwargs):
        captured.update(kwargs)
        return [
            {
                "title": "Review BFS",
                "description": "Solve three queue problems",
                "priority": 2,
            },
            {"title": "Use defaults"},
        ]

    monkeypatch.setattr(
        study_ai,
        "generate_study_checklist_items",
        fake_generate_items,
    )

    items = checklist_service.generate_checklist(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        goal_id=goal.id,
        item_count=2,
    )

    assert captured == {
        "user_name": user_a.user_name,
        "goal": status["goal"],
        "current_status": status["current_status"],
        "weak_concepts": status["weak_concepts"],
        "item_count": 2,
    }
    assert len(items) == 2
    assert items[0].user_id == user_a.id
    assert items[0].goal_id == goal.id
    assert items[0].subject == "algorithms"
    assert items[0].title == "Review BFS"
    assert items[0].description == "Solve three queue problems"
    assert items[0].priority == 2
    assert items[0].is_done is False
    assert items[1].description == ""
    assert items[1].priority == 1
    assert db.query(models.StudyChecklistItem).count() == 2


def test_list_checklist_items_only_returns_current_users_items(
    db, user_a, user_b
):
    goal_a = _create_goal(db, user_a)
    goal_b = _create_goal(db, user_b)
    db.add_all(
        [
            models.StudyChecklistItem(
                user_id=user_a.id,
                goal_id=goal_a.id,
                subject="algorithms",
                title="Mine",
                priority=1,
            ),
            models.StudyChecklistItem(
                user_id=user_b.id,
                goal_id=goal_b.id,
                subject="algorithms",
                title="Other user's",
                priority=1,
            ),
        ]
    )
    db.commit()

    items = checklist_service.list_checklist_items(
        db=db,
        user_id=user_a.id,
    )

    assert [item.title for item in items] == ["Mine"]


def test_list_checklist_items_filters_and_orders_results(db, user_a):
    goal_a = _create_goal(db, user_a)
    goal_b = _create_goal(db, user_a)
    db.add_all(
        [
            models.StudyChecklistItem(
                user_id=user_a.id,
                goal_id=goal_a.id,
                subject="algorithms",
                title="Priority two",
                priority=2,
                is_done=False,
            ),
            models.StudyChecklistItem(
                user_id=user_a.id,
                goal_id=goal_a.id,
                subject="algorithms",
                title="Priority one",
                priority=1,
                is_done=False,
            ),
            models.StudyChecklistItem(
                user_id=user_a.id,
                goal_id=goal_a.id,
                subject="algorithms",
                title="Completed",
                priority=1,
                is_done=True,
            ),
            models.StudyChecklistItem(
                user_id=user_a.id,
                goal_id=goal_b.id,
                subject="databases",
                title="Filtered out",
                priority=1,
                is_done=False,
            ),
        ]
    )
    db.commit()

    items = checklist_service.list_checklist_items(
        db=db,
        user_id=user_a.id,
        goal_id=goal_a.id,
        subject="algorithms",
    )

    assert [item.title for item in items] == [
        "Priority one",
        "Priority two",
        "Completed",
    ]


def test_update_checklist_item_rejects_other_users_item(db, user_a, user_b):
    goal = _create_goal(db, user_b)
    item = models.StudyChecklistItem(
        user_id=user_b.id,
        goal_id=goal.id,
        subject="algorithms",
        title="Private item",
        priority=1,
    )
    db.add(item)
    db.commit()

    with pytest.raises(ResourceNotFoundError):
        checklist_service.update_checklist_item(
            db=db,
            user_id=user_a.id,
            item_id=item.id,
            is_done=True,
        )


def test_update_checklist_item_sets_and_clears_completed_at(db, user_a):
    goal = _create_goal(db, user_a)
    item = models.StudyChecklistItem(
        user_id=user_a.id,
        goal_id=goal.id,
        subject="algorithms",
        title="Review BFS",
        priority=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    completed = checklist_service.update_checklist_item(
        db=db,
        user_id=user_a.id,
        item_id=item.id,
        is_done=True,
    )
    assert completed.is_done is True
    assert completed.completed_at is not None

    reopened = checklist_service.update_checklist_item(
        db=db,
        user_id=user_a.id,
        item_id=item.id,
        is_done=False,
    )
    assert reopened.is_done is False
    assert reopened.completed_at is None


def test_generate_checklist_rolls_back_when_commit_fails(
    db,
    user_a,
    monkeypatch,
):
    goal = _create_goal(db, user_a)
    monkeypatch.setattr(
        checklist_service.goal_service,
        "get_goal_status",
        lambda **kwargs: {
            "goal": {"id": goal.id, "subject": goal.subject},
            "current_status": {},
            "weak_concepts": [],
        },
    )
    monkeypatch.setattr(
        study_ai,
        "generate_study_checklist_items",
        lambda **kwargs: [{"title": "Review BFS"}],
    )
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
        checklist_service.generate_checklist(
            db=db,
            user_id=user_a.id,
            user_name=user_a.user_name,
            goal_id=goal.id,
            item_count=1,
        )

    assert rollback_called is True


@pytest.mark.parametrize(
    "generated_items",
    [
        "not a list",
        ["not a mapping"],
        [{"title": ""}],
        [{"title": "Review BFS", "description": 123}],
        [{"title": "Review BFS", "priority": 0}],
        [{"title": "Review BFS", "priority": True}],
    ],
)
def test_generate_checklist_rejects_invalid_ai_output(
    db,
    user_a,
    monkeypatch,
    generated_items,
):
    goal = _create_goal(db, user_a)
    monkeypatch.setattr(
        checklist_service.goal_service,
        "get_goal_status",
        lambda **kwargs: {
            "goal": {"id": goal.id, "subject": goal.subject},
            "current_status": {},
            "weak_concepts": [],
        },
    )
    monkeypatch.setattr(
        study_ai,
        "generate_study_checklist_items",
        lambda **kwargs: generated_items,
    )

    with pytest.raises(InvalidRequestError):
        checklist_service.generate_checklist(
            db=db,
            user_id=user_a.id,
            user_name=user_a.user_name,
            goal_id=goal.id,
            item_count=2,
        )

    assert db.query(models.StudyChecklistItem).count() == 0


def test_generate_checklist_limits_ai_output_to_requested_count(
    db,
    user_a,
    monkeypatch,
):
    goal = _create_goal(db, user_a)
    monkeypatch.setattr(
        checklist_service.goal_service,
        "get_goal_status",
        lambda **kwargs: {
            "goal": {"id": goal.id, "subject": goal.subject},
            "current_status": {},
            "weak_concepts": [],
        },
    )
    monkeypatch.setattr(
        study_ai,
        "generate_study_checklist_items",
        lambda **kwargs: [
            {"title": "First"},
            {"title": "Second"},
            {"title": "Unexpected extra item"},
        ],
    )

    items = checklist_service.generate_checklist(
        db=db,
        user_id=user_a.id,
        user_name=user_a.user_name,
        goal_id=goal.id,
        item_count=2,
    )

    assert [item.title for item in items] == ["First", "Second"]


def test_summarize_checklist_items():
    items = [
        models.StudyChecklistItem(is_done=True),
        models.StudyChecklistItem(is_done=False),
        models.StudyChecklistItem(is_done=True),
    ]

    assert checklist_service.summarize_checklist_items(items) == {
        "total_count": 3,
        "done_count": 2,
        "progress_rate": 66.67,
    }
