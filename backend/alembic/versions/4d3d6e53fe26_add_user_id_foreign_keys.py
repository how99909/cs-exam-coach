"""add user id foreign keys

Revision ID: 4d3d6e53fe26
Revises: 62cf64199a52
Create Date: 2026-08-22 18:45:15.643052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d3d6e53fe26'
down_revision: Union[str, Sequence[str], None] = '62cf64199a52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_owned_tables = [
        "study_materials",
        "wrong_answers",
        "question_feedback",
        "rag_answer_feedback",
        "exam_attempts",
        "study_goals",
        "study_checklist_items",
        "study_sessions",
        "smart_review_queue_items",
    ]
    
    for table_name in user_owned_tables:
        op.add_column(
            table_name,
            sa.Column(
                "user_id",
                sa.Integer(),
                nullable=True,
            ),
        )
        
        op.create_foreign_key(
            f"fk_{table_name}_user_id_users",
            table_name,
            "users",
            ["user_id"],
            ["id"],
        )
        
        op.create_index(
            f"ix_{table_name}_user_id",
            table_name,
            ["user_id"],
            unique=False,
        )
        
    for table_name in user_owned_tables:
        op.execute(
            f"""
            UPDATE {table_name} AS target
            SET user_id = users.id
            FROM users
            WHERE target.user_name = users.user_name
              AND target.user_id IS NULL
            """
        )


def downgrade() -> None:
    user_owned_tables = [
        "study_materials",
        "wrong_answers",
        "question_feedback",
        "rag_answer_feedback",
        "exam_attempts",
        "study_goals",
        "study_checklist_items",
        "study_sessions",
        "smart_review_queue_items",
    ]
    
    for table_name in reversed(user_owned_tables):
        op.drop_index(
            f"ix_{table_name}_user_id",
            table_name=table_name,
        )
        
        op.drop_constraint(
            f"fk_{table_name}_user_id_users",
            table_name,
            type_="foreignkey",
        )
        
        op.drop_column(
            table_name,
            "user_id",
        )