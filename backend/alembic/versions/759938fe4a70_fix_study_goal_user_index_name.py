"""fix study goal user index name

Revision ID: 759938fe4a70
Revises: e1d39763c3a4
Create Date: 2026-08-26 10:50:54.841672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '759938fe4a70'
down_revision: Union[str, Sequence[str], None] = 'e1d39763c3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        "ix_study_goals_user_exam_dat",
        table_name="study_goals"
    )
    
    op.create_index(
        "ix_study_goals_user_exam_date",
        "study_goals",
        ["user_id", "exam_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_study_goals_user_exam_date",
        table_name="study-goals",
    )

    op.create_index(
        "ix_study_goals_user_exam_dat",
        "study_goals",
        ["user_id", "exam_date"],
        unique=False,
    )