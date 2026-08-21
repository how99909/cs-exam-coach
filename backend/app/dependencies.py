from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import auth_service, models
from app.database import get_db

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = auth_service.decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않거나 만료된 인증 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_name = payload.get("sub")
    
    if not isinstance(user_name, str) or not user_name:
        raise HTTPException(
            status_code=401,
            detail="토큰에 사용자 정보가 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = (
        db.query(models.User)
        .filter(models.User.user_name == user_name)
        .first()
    )
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user
