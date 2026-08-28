import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.dependencies import get_current_user
from app.main import app


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    
    
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    yield
    
    Base.metadata.drop_all(bind=engine)
    
    
@pytest.fixture
def db():
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        
        
@pytest.fixture
def client(db):
    def override_get_db():
        yield db
        
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()
    
    
@pytest.fixture
def user_a(db):
    user = models.User(
        user_name="user_a",
        email="user_a@example.com",
        hashed_password="test-password-hash",
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def user_b(db):
    user = models.User(
        user_name="user_b",
        email="user_b@example.com",
        hashed_password="test-password-hash",
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def auth_client(client, user_a):
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    yield client
    
    app.dependency_overrides.pop(
        get_current_user,
        None,
    )
    
    
@pytest.fixture
def auth_as():
    def _auth_as(user):
        app.dependency_overrides[get_current_user] = lambda: user
        
    yield _auth_as
    
    app.dependency_overrides.pop(
        get_current_user,
        None,
    )