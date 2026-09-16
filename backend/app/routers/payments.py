"""
Payment endpoints – Stripe test-mode integration.
"""

from fastapi import APIRouter, Depends, Request, Header, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services import payments as pay

router = APIRouter(prefix="/payments", tags=["Payments (Stripe)"])


class DepositRequest(BaseModel):
    account_id: int
    amount: float = Field(..., gt=0.49, le=100000)
    currency: str = "usd"


class AchSetupRequest(BaseModel):
    account_id: int


@router.get("/config")
def payment_config():
    return pay.get_publishable_key()


@router.post("/deposit-intent")
def create_deposit(
    body: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    amount_cents = int(round(body.amount * 100))
    return pay.create_deposit_intent(
        db, current_user, body.account_id, amount_cents, body.currency
    )


@router.post("/ach-setup")
def ach_setup(
    body: AchSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return pay.create_ach_setup(db, current_user, body.account_id)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    if not stripe_signature:
        raise HTTPException(400, "Missing Stripe-Signature header")
    payload = await request.body()
    return pay.handle_stripe_webhook(payload, stripe_signature, db)
