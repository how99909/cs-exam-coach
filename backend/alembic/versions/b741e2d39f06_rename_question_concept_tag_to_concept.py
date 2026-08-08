"""Rename question concept_tag to concept

Revision ID: b741e2d39f06
Revises: 8c9f5b1d7a42
Create Date: 2026-08-08

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b741e2d39f06"
down_revision: Union[str, Sequence[str], None] = "8c9f5b1d7a42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("questions", "concept_tag", new_column_name="concept")


def downgrade() -> None:
    op.alter_column("questions", "concept", new_column_name="concept_tag")
