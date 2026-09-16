"""
BaaS API surface — Unit-inspired Hold / Move / Spend / Lend.
Simulation only.
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.baas_schemas import (
    DepositAccountCreate, DepositAccountOut,
    PaymentCreate, PaymentOut,
    BaasCardCreate, BaasCardOut,
    CreditAccountCreate, CreditAccountOut,
    BaasDashboard,
)
from app.services import baas_service as svc

router = APIRouter(prefix="/baas", tags=["BaaS (Unit-style simulation)"])


@router.post("/accounts", response_model=DepositAccountOut, status_code=201)
def open_account(
    body: DepositAccountCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.create_deposit_account(db, user, body)


@router.get("/accounts", response_model=List[DepositAccountOut])
def list_accounts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.list_deposit_accounts(db, user.id)


@router.post("/payments", response_model=PaymentOut, status_code=201)
def create_payment(
    body: PaymentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.create_payment(db, user, body)


@router.get("/payments", response_model=List[PaymentOut])
def list_payments(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.list_payments(db, user.id, limit)


@router.post("/cards", response_model=BaasCardOut, status_code=201)
def issue_card(
    body: BaasCardCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.create_baas_card(db, user, body)


@router.get("/cards", response_model=List[BaasCardOut])
def list_cards(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.list_baas_cards(db, user.id)


@router.post("/cards/{card_id}/toggle-freeze", response_model=BaasCardOut)
def toggle_freeze(
    card_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.freeze_baas_card(db, user, card_id)


@router.post("/credit-accounts", response_model=CreditAccountOut, status_code=201)
def open_credit(
    body: CreditAccountCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.create_credit_account(db, user, body)


@router.get("/credit-accounts", response_model=List[CreditAccountOut])
def list_credit(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.list_credit_accounts(db, user.id)


@router.get("/dashboard", response_model=BaasDashboard)
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.baas_dashboard(db, user.id)
