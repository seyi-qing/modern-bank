"""
Authentication & user management service.
Handles registration (with simulated e-KYC), login, token refresh.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserRole, Account, AccountType
from app.models.schemas import UserRegister, UserLogin
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.core.config import settings
import random
import string


def generate_account_number() -> str:
    return "".join(random.choices(string.digits, k=12))


def register_user(db: Session, data: UserRegister) -> User:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    if len(data.password) < settings.MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password too short")

    user = User(
        email=data.email.lower().strip(),
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name.strip(),
        phone=data.phone,
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        kyc_status="verified",
    )
    db.add(user)
    db.flush()

    account = Account(
        user_id=user.id,
        account_number=generate_account_number(),
        account_type=AccountType.CHECKING,
        balance=100.0,
        currency=settings.DEFAULT_CURRENCY,
    )
    db.add(account)

    savings = Account(
        user_id=user.id,
        account_number=generate_account_number(),
        account_type=AccountType.SAVINGS,
        balance=0.0,
        currency=settings.DEFAULT_CURRENCY,
    )
    db.add(savings)

    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: UserLogin) -> User:
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    return user


def create_tokens_for_user(user: User) -> dict:
    payload = {"sub": str(user.id), "role": user.role.value, "email": user.email}
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
    }
