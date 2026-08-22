"""finalize user id ownership

Revision ID: e1d39763c3a4
Revises: 4d3d6e53fe26
Create Date: 2026-08-22 20:45:57.821846

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1d39763c3a4'
down_revision: Union[str, Sequence[str], None] = '4d3d6e53fe26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    
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
        null_count = connection.execute(
            sa.text(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE user_id IS NULL
                """
            )
        ).scalar()
        
        if null_count:
            raise RuntimeError(
                f"{table_name}에 user_id NULL 데이터가"
                f"{null_count}개 존재합니다."
            )
            
    orphan_question_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM questions q
            LEFT JOIN study_materials m
                ON q.material_id = m.id
            WHERE m.id IS NULL
            """
        )
    ).scalar()
    
    if orphan_question_count:
        raise RuntimeError(
            "StudyMaterial이 없는 Question이 존재합니다."
        )
        
    old_indexes = [
        ("study_materials", "ix_study_materials_user_subject_created"),
        ("wrong_answers", "ix_wrong_answers_user_created"),
        ("exam_attempts", "ix_exam_attempts_user_subject_created"),
        ("study_goals", "ix_study_goals_user_exam_date"),
        ("study_checklist_items", "ix_checklist_user_goal_done"),
        ("study_sessions", "ix_study_sessions_user_subject_created"),
        ("smart_review_queue_items", "ix_review_queue_user_done_priority"),
    ]
    
    for table_name, index_name in old_indexes:
        op.drop_index(
            index_name,
            table_name=table_name,
        )
        
    for table_name in user_owned_tables:
        op.alter_column(
            table_name,
            "user_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        
    for table_name in user_owned_tables:
        op.drop_column(
            table_name,
            "user_name",
        )
        
    op.create_index(
        "ix_study_materials_user_subject_created",
        "study_materials",
        ["user_id", "subject", "created_at"],
    )
    
    op.create_index(
        "ix_wrong_answers_user_created",
        "wrong_answers",
        ["user_id", "created_at"],
    )
    
    op.create_index(
        "ix_question_feedback_user_question",
        "question_feedback",
        ["user_id", "question_id"],
    )
    
    op.create_index(
        "ix_rag_feedback_user_subject_created",
        "rag_answer_feedback",
        ["user_id", "subject", "created_at"],
    )
    
    op.create_index(
        "ix_exam_attempts_user_subject_created",
        "exam_attempts",
        ["user_id", "subject", "created_at"],
    )
    
    op.create_index(
        "ix_study_goals_user_exam_dat",
        "study_goals",
        ["user_id", "exam_date"],
    )
    
    op.create_index(
        "ix_checklist_user_goal_done",
        "study_checklist_items",
        ["user_id", "goal_id", "is_done"],
    )
    
    op.create_index(
        "ix_study_sessions_user_subject_created",
        "study_sessions",
        ["user_id", "subject", "created_at"],
    )
    
    op.create_index(
        "ix_review_queue_user_done_priority",
        "smart_review_queue_items",
        ["user_id", "is_done", "priority"],
    )
    
    op.create_foreign_key(
        "fk_questions_material_id_study_materials",
        "questions",
        "study_materials",
        ["material_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
