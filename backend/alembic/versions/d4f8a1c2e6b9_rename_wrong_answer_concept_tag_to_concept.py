"""Rename wrong answer concept_tag to concept

Revision ID: d4f8a1c2e6b9
Revises: b7dd475b005f
Create Date: 2026-08-16

"""
from typing import Sequence, Union

from alembic import op


revision: str = "d4f8a1c2e6b9"
down_revision: Union[str, Sequence[str], None] = "b7dd475b005f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("wrong_answers", "concept_tag", new_column_name="concept")


def downgrade() -> None:
    op.alter_column("wrong_answers", "concept", new_column_name="concept_tag")
