"""
Admin-only endpoints: system stats, user management, flagged transactions.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User, Transaction
from app.models.schemas import AdminStats, UserOut, AdminUserUpdate, TransactionOut
from app.services.banking_service import get_admin_stats

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStats)
def stats(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return get_admin_stats(db)


@router.get("/users", response_model=List[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).offset(skip).limit(limit).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.kyc_status is not None:
        user.kyc_status = data.kyc_status
    if data.role is not None:
        user.role = data.role
    db.commit()
    db.refresh(user)
    return user


@router.get("/transactions/flagged", response_model=List[TransactionOut])
def flagged_transactions(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .filter(Transaction.is_flagged == True)
        .order_by(Transaction.created_at.desc())
        .limit(100)
        .all()
    )


@router.get("/transactions", response_model=List[TransactionOut])
def all_transactions(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
