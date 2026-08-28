from app import auth_service


def test_password_hash_and_verify():
    password = "password123"
    
    hashed = auth_service.hash_password(password)
    
    assert hashed != password
    assert auth_service.verify_password(
        password,
        hashed,
    )
    assert not auth_service.verify_password(
        "wrong-password",
        hashed,
    )
    
    
def test_create_and_decode_access_token():
    token = auth_service.create_access_token(
        {
            "sub": "student1",
        }
    )
    
    payload = auth_service.decode_access_token(token)
    
    assert payload is not None
    assert payload["sub"] == "student1"
    assert "exp" in payload
    
    
def test_decode_invalid_token_returns_none():
    payload = auth_service.decode_access_token(
        "invalid-token"
    )
    
    assert payload is None