"""
Authentication endpoints: register, login, refresh, me.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.schemas import UserRegister, UserOut, Token, UserLogin
from app.models.user import User
from app.services.auth_service import register_user, authenticate_user, create_tokens_for_user
from app.core.security import decode_token, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    user = register_user(db, data)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, UserLogin(email=form_data.username, password=form_data.password))
    return create_tokens_for_user(user)


@router.post("/login/json", response_model=Token)
def login_json(data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, data)
    return create_tokens_for_user(user)


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return create_tokens_for_user(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
