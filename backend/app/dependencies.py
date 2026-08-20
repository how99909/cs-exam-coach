from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import auth_service, models
from app.database import get_db

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    token = credentials.credentials
    payload = auth_service.decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 인증 토큰입니다.",
        )
        
    user_name = payload.get("sub")
    
    if not user_name:
        raise HTTPException(
            status_code=401,
            detail="토큰에 사용자 정보가 없습니다.",
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
        )
        
    return user