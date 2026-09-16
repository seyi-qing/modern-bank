"""
Stripe integration (test-mode by default).
Live mode gated by ENABLE_LIVE_PAYMENTS.
"""

from __future__ import annotations

import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User, Account, Transaction, TransactionType, TransactionStatus, Notification
import uuid
from datetime import datetime, timezone


def _configure_stripe() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured. Set STRIPE_SECRET_KEY (sk_test_...).",
        )
    is_live_key = settings.STRIPE_SECRET_KEY.startswith("sk_live_")
    if is_live_key and not settings.ENABLE_LIVE_PAYMENTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live Stripe keys detected but ENABLE_LIVE_PAYMENTS is false.",
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY


def get_publishable_key() -> dict:
    if not settings.STRIPE_PUBLISHABLE_KEY:
        raise HTTPException(503, "STRIPE_PUBLISHABLE_KEY is not set")
    return {
        "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "live_mode_enabled": settings.ENABLE_LIVE_PAYMENTS
        and settings.STRIPE_SECRET_KEY.startswith("sk_live_"),
        "mode": "live" if settings.STRIPE_SECRET_KEY.startswith("sk_live_") else "test",
    }


def create_deposit_intent(
    db: Session, user: User, account_id: int, amount_cents: int, currency: str = "usd",
) -> dict:
    _configure_stripe()
    if amount_cents < 50:
        raise HTTPException(400, "Minimum amount is $0.50")
    account = db.query(Account).filter(
        Account.id == account_id, Account.user_id == user.id, Account.is_active == True
    ).first()
    if not account:
        raise HTTPException(404, "Account not found")

    idempotency_key = f"deposit-{user.id}-{account_id}-{uuid.uuid4().hex[:12]}"
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency.lower(),
            metadata={
                "user_id": str(user.id),
                "account_id": str(account_id),
                "type": "deposit",
                "internal_ref": idempotency_key,
            },
            automatic_payment_methods={"enabled": True},
            idempotency_key=idempotency_key,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(400, f"Stripe error: {str(e)}")

    tx = Transaction(
        user_id=user.id,
        account_id=account.id,
        amount=amount_cents / 100.0,
        currency=currency.upper(),
        type=TransactionType.DEPOSIT,
        status=TransactionStatus.PENDING,
        description="Stripe deposit (pending)",
        reference=intent.id,
    )
    db.add(tx)
    db.commit()
    return {
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
        "amount": amount_cents / 100.0,
        "currency": currency.upper(),
        "status": intent.status,
    }


def create_ach_setup(db: Session, user: User, account_id: int) -> dict:
    _configure_stripe()
    account = db.query(Account).filter(
        Account.id == account_id, Account.user_id == user.id, Account.is_active == True
    ).first()
    if not account:
        raise HTTPException(404, "Account not found")
    try:
        setup = stripe.SetupIntent.create(
            payment_method_types=["us_bank_account"],
            metadata={"user_id": str(user.id), "account_id": str(account_id)},
        )
    except stripe.error.StripeError as e:
        raise HTTPException(400, f"Stripe error: {str(e)}")
    return {"client_secret": setup.client_secret, "setup_intent_id": setup.id}


def handle_stripe_webhook(payload: bytes, sig_header: str, db: Session) -> dict:
    _configure_stripe()
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "STRIPE_WEBHOOK_SECRET not set")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(400, f"Webhook error: {e}")

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        ref = intent["id"]
        tx = db.query(Transaction).filter(Transaction.reference == ref).first()
        if tx and tx.status == TransactionStatus.PENDING:
            account = db.query(Account).filter(Account.id == tx.account_id).first()
            if account:
                account.balance = round(account.balance + tx.amount, 2)
                tx.status = TransactionStatus.COMPLETED
                tx.description = "Stripe deposit (completed)"
                db.add(Notification(
                    user_id=tx.user_id,
                    title="Deposit received",
                    message=f"${tx.amount:.2f} was added to your account.",
                    type="transfer",
                ))
                db.commit()
    return {"received": True}
