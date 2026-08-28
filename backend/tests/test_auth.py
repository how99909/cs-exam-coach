from datetime import datetime, timedelta, timezone

from jose import jwt

from app import auth_service, models
from app.core.config import settings


VALID_USER = {
    "user_name": "student1",
    "email": "student1@example.com",
    "password": "password123",
}


def register_user(client, **overrides):
    payload = {
        **VALID_USER,
        **overrides,
    }
    
    return client.post(
        "/auth/register",
        json=payload,
    )
    
    
def login_user(
    client,
    user_name="student1",
    password="password123",
):
    return client.post(
        "/auth/login",
        json={
            "user_name": user_name,
            "password": password,
        },
    )
    
    
def bearer(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }
    
    
def test_register_success(client, db):
    response = register_user(client)
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["success"] is True
    assert data["user"]["user_name"] == "student1"
    assert data["user"]["email"] == "student1@example.com"
    
    user = (
        db.query(models.User)
        .filter(models.User.user_name == "student1")
        .first()
    )
    
    assert user is not None
    
    assert user.hashed_password != "password123"
    
    assert auth_service.verify_password(
        "password123",
        user.hashed_password,
    )
    
    
def test_duplicate_user_name_is_rejected(client):
    register_user(client)
    
    response = register_user(
        client,
        email="another@example.com",
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "이미 사용 중인 user_name입니다."
    )
    
    
def test_duplicate_email_is_rejected(client):
    register_user(client)
    
    response = register_user(
        client,
        user_name="student2",
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "이미 사용 중인 email입니다."
    )
    
    
def test_login_success(client):
    register_user(client)
    
    response = login_user(client)
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["token_type"] == "bearer"
    assert data["user_name"] == "student1"
    assert isinstance(data["access_token"], str)
    assert data["access_token"]
    
    
def test_login_with_wrong_password_is_rejected(client):
    register_user(client)
    
    response = login_user(
        client,
        password="wrong-password",
    )
    
    assert response.status_code == 401
    
    
def test_login_with_unknown_user_is_rejected(client):
    response = login_user(
        client,
        user_name="unknown",
    )
    
    assert response.status_code == 401
    
    
def test_me_with_valid_token(client):
    register_user(client)
    
    login_response = login_user(client)
    token = login_response.json()["access_token"]
    
    
    response = client.get(
        "/auth/me",
        headers=bearer(token),
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["success"] is True
    assert data["user"]["user_name"] == "student1"
    assert data["user"]["email"] == "student1@example.com"
    
    
def test_me_without_token_is_rejected(client):
    response = client.get("/auth/me")
    
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    
    
def test_me_with_invalid_token_is_rejected(client):
    response = client.get(
        "/auth/me",
        headers=bearer("not-a-valid-jwt"),
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == (
        "유효하지 않거나 만료된 인증 토큰입니다."
    )
    
    
def test_me_with_expired_token_is_rejected(client):
    register_user(client)
    
    expired_token = jwt.encode(
        {
            "sub": "student1",
            "exp": (
                datetime.now(timezone.utc) - timedelta(minutes=1)
            ),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    response = client.get(
        "/auth/me",
        headers=bearer(expired_token)
    )
    
    assert response.status_code == 401
    
    
def test_me_with_token_without_subject_is_rejected(client):
    token = jwt.encode(
        {
            "exp": (
                datetime.now(timezone.utc) + timedelta(minutes=5)
            ),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    response = client.get(
        "/auth/me",
        headers=bearer(token),
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == (
        "토큰에 사용자 정보가 없습니다."
    )
    
    
def test_token_for_deleted_user_is_rejected(client, db):
    register_user(client)
    
    login_response = login_user(client)
    token = login_response.json()["access_token"]
    
    user = (
        db.query(models.User)
        .filter(models.User.user_name == "student1")
        .first()
    )
    
    db.delete(user)
    db.commit()
    
    response = client.get(
        "/auth/me",
        headers=bearer(token)
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == (
        "사용자를 찾을 수 없습니다."
    )