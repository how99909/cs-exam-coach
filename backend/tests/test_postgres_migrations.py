import os
from pathlib import Path

import pytest

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


pytestmark = pytest.mark.postgres


BACKEND_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"


USER_OWNED_TABLES = [
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

def get_test_database_url():
    database_url = os.getenv("TEST_DATABASE_URL")
    
    if not database_url:
        pytest.skip(
            "TEST_DATABASE_URL is not configured."
        )
        
    parsed = make_url(database_url)
    database_name = parsed.database or ""
    
    if not database_name.endswith("_test"):
        raise RuntimeError(
            "PostgreSQL migration test는 "
            "*_test 데이터베이스에서만 실행할 수 있습니다."
        )
        
    return database_url


def reset_public_schema(engine):
    with engine.begin() as connection:
        connection.execute(
            text("DROP SCHEMA IF EXISTS public CASCADE")
        )
        connection.execute(
            text("CREATE SCHEMA public")
        )
        
        
@pytest.fixture(scope="module")
def migrated_postres():
    database_url = get_test_database_url()
    
    engine = create_engine(database_url)
    
    reset_public_schema(engine)
    
    previous_database_url = os.environ.get(
        "DATABASE_URL"
    )
    
    os.environ["DATABASE_URL"] = database_url
    
    config = Config(str(ALEMBIC_INI))
    
    try:
        command.upgrade(
            config,
            "head",
        )
    finally:
        if previous_database_url is None:
            os.environ.pop(
                "DATABASE_URL",
                None,
            )
        else:
            os.environ["DATABASE_URL"] = (
                previous_database_url
            )
            
    yield engine
    
    reset_public_schema(engine)
    engine.dispose()
    
    
def test_database_is_at_alembic_head(
    migrated_postres,
):
    config = Config(str(ALEMBIC_INI))
    
    script = ScriptDirectory.from_config(config)
    
    expected_head = script.get_current_head()
    
    with migrated_postres.connect() as connection:
        context = MigrationContext.configure(
            connection
        )
        
        current_revision = (
            context.get_current_revision()
        )
        
    assert current_revision == expected_head
    
    
def test_user_owned_tables_use_required_user_id(
    migrated_postres,
):
    inspector = inspect(migrated_postres)
    
    for table_name in USER_OWNED_TABLES:
        columns = {
            column["name"]: column
            for column
            in inspector.get_columns(table_name)
        }
        
        assert "user_id" in columns
        
        assert columns["user_id"]["nullable"] is False
        
        assert "user_name" not in columns
        
        foreign_keys = (
            inspector.get_foreign_keys(
                table_name
            )
        )
        
        assert any(
            fk["constrained_columns"] == ["user_id"] and fk["referred_table"] == "users" and fk["referred_columns"] == ["id"]
            for fk in foreign_keys
        )
        
        
def test_question_material_id_has_foreign_key(
    migrated_postres,
):
    inspector = inspect(migrated_postres)
    
    foreign_keys = inspector.get_foreign_keys(
        "questions"
    )
    
    assert any(
        fk["constrained_columns"] == ["material_id"] and fk["referred_table"] == "study_materials" and fk["referred_columns"] == ["id"]
        for fk in foreign_keys
    )
    
    
def test_study_goal_index_name_is_correct(
    migrated_postres,
):
    inspector = inspect(migrated_postres)
    
    indexes = inspector.get_indexes(
        "study_goals"
    )
    
    index_names = {
        item["name"]
        for item in indexes
    }
    
    assert(
        "ix_study_goals_user_exam_date"
        in index_names
    )
    
    assert (
        "ix_study_goals_user_exam_dat"
        not in index_names
    )
    
    
def test_alembic_has_no_model_schema_drift(
    migrated_postres,
):
    database_url = get_test_database_url()
    
    previous_database_url = os.environ.get(
        "DATABASE_URL"
    )
    
    os.environ["DATABASE_URL"] = database_url
    
    config = Config(str(ALEMBIC_INI))
    
    try:
        command.check(config)
    finally:
        if previous_database_url is None:
            os.environ.pop(
                "DATABASE_URL",
                None,
            )
        else:
            os.environ["DATABASE_URL"] = (
                previous_database_url
            )
