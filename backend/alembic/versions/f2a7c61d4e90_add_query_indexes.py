"""add query indexes

Revision ID: f2a7c61d4e90
Revises: c56422efc323
"""

from typing import Sequence, Union

from alembic import op


revision: str = "f2a7c61d4e90"
down_revision: Union[str, Sequence[str], None] = "c56422efc323"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_study_materials_user_subject_created",
        "study_materials",
        ["user_name", "subject", "created_at"],
    )
    op.create_index(
        "ix_wrong_answers_user_created",
        "wrong_answers",
        ["user_name", "created_at"],
    )
    op.create_index(
        "ix_exam_attempts_user_subject_created",
        "exam_attempts",
        ["user_name", "subject", "created_at"],
    )
    op.create_index(
        "ix_study_goals_user_exam_date",
        "study_goals",
        ["user_name", "exam_date"],
    )
    op.create_index(
        "ix_checklist_user_goal_done",
        "study_checklist_items",
        ["user_name", "goal_id", "is_done"],
    )
    op.create_index(
        "ix_study_sessions_user_subject_created",
        "study_sessions",
        ["user_name", "subject", "created_at"],
    )
    op.create_index(
        "ix_review_queue_user_done_priority",
        "smart_review_queue_items",
        ["user_name", "is_done", "priority"],
    )


def downgrade() -> None:
    op.drop_index("ix_review_queue_user_done_priority", table_name="smart_review_queue_items")
    op.drop_index("ix_study_sessions_user_subject_created", table_name="study_sessions")
    op.drop_index("ix_checklist_user_goal_done", table_name="study_checklist_items")
    op.drop_index("ix_study_goals_user_exam_date", table_name="study_goals")
    op.drop_index("ix_exam_attempts_user_subject_created", table_name="exam_attempts")
    op.drop_index("ix_wrong_answers_user_created", table_name="wrong_answers")
    op.drop_index("ix_study_materials_user_subject_created", table_name="study_materials")
