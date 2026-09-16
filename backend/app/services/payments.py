"""
Stripe integration (test-mode by default).
"""

from __future__ import annotations

import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User, Account, Transaction, TransactionType, TransactionStatus, Notification
import uuid


def _configure_stripe() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured. Set STRIPE_SECRET_KEY (sk_test_...) in the environment.",
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
        "live_mode_enabled": settings.ENABLE_LIVE_PAYMENTS and settings.STRIPE_SECRET_KEY.startswith("sk_live_"),
        "mode": "live" if settings.STRIPE_SECRET_KEY.startswith("sk_live_") else "test",
    }


def create_deposit_intent(db: Session, user: User, account_id: int, amount_cents: int, currency: str = "usd") -> dict:
    _configure_stripe()
    if amount_cents < 50:
        raise HTTPException(400, "Minimum amount is $0.50")
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user.id, Account.is_active == True).first()
    if not account:
        raise HTTPException(404, "Account not found")

    idempotency_key = f"deposit-{user.id}-{account_id}-{uuid.uuid4().hex[:12]}"
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency.lower(),
            metadata={"user_id": str(user.id), "account_id": str(account_id), "type": "deposit", "internal_ref": idempotency_key},
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
        is_flagged=False,
        fraud_score=0.0,
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
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user.id, Account.is_active == True).first()
    if not account:
        raise HTTPException(404, "Account not found")
    try:
        setup_intent = stripe.SetupIntent.create(
            payment_method_types=["us_bank_account"],
            metadata={"user_id": str(user.id), "account_id": str(account_id), "type": "ach_setup"},
        )
    except stripe.error.StripeError as e:
        raise HTTPException(400, f"Stripe error: {str(e)}")
    return {"client_secret": setup_intent.client_secret, "setup_intent_id": setup_intent.id}


def handle_stripe_webhook(payload: bytes, sig_header: str, db: Session) -> dict:
    _configure_stripe()
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "STRIPE_WEBHOOK_SECRET not configured")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        return _credit_from_intent(db, event["data"]["object"])
    elif event["type"] == "payment_intent.payment_failed":
        return _mark_failed(db, event["data"]["object"])
    elif event["type"] == "setup_intent.succeeded":
        return {"status": "setup_succeeded", "id": event["data"]["object"]["id"]}
    return {"status": "ignored", "type": event["type"]}


def _credit_from_intent(db: Session, intent: dict) -> dict:
    pi_id = intent["id"]
    meta = intent.get("metadata") or {}
    user_id = int(meta.get("user_id", 0))
    account_id = int(meta.get("account_id", 0))
    amount = intent["amount"] / 100.0
    if not user_id or not account_id:
        return {"status": "missing_metadata"}

    tx = db.query(Transaction).filter(Transaction.reference == pi_id, Transaction.status == TransactionStatus.PENDING).first()
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"status": "account_not_found"}

    if tx:
        tx.status = TransactionStatus.COMPLETED
        tx.description = "Stripe deposit (confirmed)"
    else:
        tx = Transaction(
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            currency=intent.get("currency", "usd").upper(),
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            description="Stripe deposit (confirmed)",
            reference=pi_id,
        )
        db.add(tx)

    account.balance = round(account.balance + amount, 2)
    db.add(Notification(user_id=user_id, title="Deposit received", message=f"${amount:.2f} has been added to your account via Stripe.", type="transfer"))
    db.commit()
    return {"status": "credited", "amount": amount, "account_id": account_id}


def _mark_failed(db: Session, intent: dict) -> dict:
    pi_id = intent["id"]
    tx = db.query(Transaction).filter(Transaction.reference == pi_id, Transaction.status == TransactionStatus.PENDING).first()
    if tx:
        tx.status = TransactionStatus.FAILED
        tx.description = "Stripe deposit failed"
        db.commit()
    return {"status": "marked_failed", "id": pi_id}
