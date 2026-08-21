from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import auth_service, models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(
    request: schemas.UserCreateRequest,
    db: Session = Depends(get_db),
):
    if len(request.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="비밀번호는 UTF-8 기준 72바이트 이하여야 합니다.",
        )

    existing_user = (
        db.query(models.User)
        .filter(models.User.user_name == request.user_name)
        .first()
    )
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="이미 사용 중인 user_name입니다.",
        )
        
    if request.email:
        existing_email = (
            db.query(models.User)
            .filter(models.User.email == request.email)
            .first()
        )
        
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="이미 사용 중인 email입니다.",
            )
            
    user = models.User(
        user_name=request.user_name,
        email=request.email,
        hashed_password=auth_service.hash_password(request.password)
    )
    
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="이미 사용 중인 user_name 또는 email입니다.",
        )
    db.refresh(user)
    
    return {
        "success": True,
        "message": "회원가입이 완료되었습니다.",
        "user": {
            "id": user.id,
            "user_name": user.user_name,
            "email": user.email,
            "created_at": user.created_at,
        },
    }
    
    
@router.post("/login", response_model=schemas.TokenResponse)
def login(
    request: schemas.UserLoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.user_name == request.user_name)
        .first()
    )
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="user_name 또는 비밀번호가 올바르지 않습니다.",
        )
        
    if not auth_service.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="user_name 또는 비밀번호가 올바르지 않습니다.",
        )
        
    access_token = auth_service.create_access_token(
        data={"sub": user.user_name}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": user.user_name,
    }
    
    
@router.get("/me")
def me(
    current_user: models.User = Depends(get_current_user),
):
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "user_name": current_user.user_name,
            "email": current_user.email,
            "created_at": current_user.created_at,
        },
    }
