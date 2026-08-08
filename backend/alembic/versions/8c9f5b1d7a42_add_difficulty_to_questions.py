"""Add difficulty to questions

Revision ID: 8c9f5b1d7a42
Revises: 2dc3a56029bc
Create Date: 2026-08-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c9f5b1d7a42"
down_revision: Union[str, Sequence[str], None] = "2dc3a56029bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column(
            "difficulty",
            sa.String(length=50),
            nullable=False,
            server_default="medium",
        ),
    )


def downgrade() -> None:
    op.drop_column("questions", "difficulty")
