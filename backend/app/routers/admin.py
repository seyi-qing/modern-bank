"""
Admin / control-plane endpoints — gated by RBAC permissions.
Never exposes balance-edit operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_staff, require_perm
from app.core.permissions import Permission
from app.models.user import User, Transaction, Account, UserRole
from app.models.schemas import AdminStats, UserOut, AdminUserUpdate, TransactionOut
from app.models.schemas_ops import CardRequestOut, CardRequestReview, Customer360
from app.services.banking_service import get_admin_stats
from app.services.audit import write_audit
from app.services.card_request_service import list_pending_card_requests, review_card_request
from app.services.customer_360 import search_users, get_customer_360

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStats)
def stats(
    staff: User = Depends(require_perm(Permission.STATS_READ)),
    db: Session = Depends(get_db),
):
    return get_admin_stats(db)


@router.get("/users", response_model=List[UserOut])
def list_users(
    q: Optional[str] = Query(None, description="Search email, name, or phone"),
    skip: int = 0,
    limit: int = 50,
    staff: User = Depends(require_perm(Permission.USERS_READ)),
    db: Session = Depends(get_db),
):
    return search_users(db, q, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=Customer360)
def customer_360(
    user_id: int,
    staff: User = Depends(require_perm(Permission.USERS_READ)),
    db: Session = Depends(get_db),
):
    return get_customer_360(db, user_id)


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    request: Request,
    staff: User = Depends(require_perm(Permission.USERS_WRITE)),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    before = {
        "is_active": user.is_active,
        "kyc_status": user.kyc_status,
        "role": user.role.value,
    }

    if data.role is not None:
        if staff.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admin may change user roles")
        user.role = data.role

    if data.is_active is not None:
        user.is_active = data.is_active
    if data.kyc_status is not None:
        user.kyc_status = data.kyc_status

    write_audit(
        db,
        actor=staff,
        action="ADMIN_UPDATE_USER",
        resource_type="user",
        resource_id=user.id,
        reason="Control-plane user update",
        before=before,
        after={
            "is_active": user.is_active,
            "kyc_status": user.kyc_status,
            "role": user.role.value,
        },
        request=request,
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/accounts/{account_id}/freeze", response_model=dict)
def freeze_account(
    account_id: int,
    request: Request,
    staff: User = Depends(require_perm(Permission.ACCOUNTS_FREEZE)),
    db: Session = Depends(get_db),
):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    before = {"is_active": acc.is_active}
    acc.is_active = False
    write_audit(
        db,
        actor=staff,
        action="ACCOUNT_FREEZE",
        resource_type="account",
        resource_id=acc.id,
        reason="Staff freeze",
        before=before,
        after={"is_active": False},
        request=request,
    )
    db.commit()
    return {"account_id": acc.id, "is_active": False}


@router.post("/accounts/{account_id}/unfreeze", response_model=dict)
def unfreeze_account(
    account_id: int,
    request: Request,
    staff: User = Depends(require_perm(Permission.ACCOUNTS_FREEZE)),
    db: Session = Depends(get_db),
):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    before = {"is_active": acc.is_active}
    acc.is_active = True
    write_audit(
        db,
        actor=staff,
        action="ACCOUNT_UNFREEZE",
        resource_type="account",
        resource_id=acc.id,
        reason="Staff unfreeze",
        before=before,
        after={"is_active": True},
        request=request,
    )
    db.commit()
    return {"account_id": acc.id, "is_active": True}


@router.get("/card-requests", response_model=List[CardRequestOut])
def pending_card_requests(
    staff: User = Depends(require_perm(Permission.CARDS_OPS)),
    db: Session = Depends(get_db),
):
    return list_pending_card_requests(db)


@router.post("/card-requests/{request_id}/review", response_model=CardRequestOut)
def review_card_req(
    request_id: int,
    data: CardRequestReview,
    request: Request,
    staff: User = Depends(require_perm(Permission.CARDS_OPS)),
    db: Session = Depends(get_db),
):
    before = {"status": "pending"}
    result = review_card_request(db, request_id, data.action, data.reason, staff)
    write_audit(
        db,
        actor=staff,
        action="CARD_REQUEST_REVIEW",
        resource_type="card_request",
        resource_id=result.id,
        reason=data.reason,
        before=before,
        after={"status": result.status.value, "issued_card_id": result.issued_card_id},
        request=request,
    )
    db.commit()
    db.refresh(result)
    return result


@router.get("/transactions/flagged", response_model=List[TransactionOut])
def flagged_transactions(
    staff: User = Depends(require_perm(Permission.TRANSACTIONS_FLAGGED)),
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
    staff: User = Depends(require_perm(Permission.TRANSACTIONS_READ)),
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/me/permissions")
def my_permissions(staff: User = Depends(get_current_staff)):
    from app.core.permissions import permissions_for

    return {
        "role": staff.role.value,
        "permissions": sorted(p.value for p in permissions_for(staff.role)),
    }
