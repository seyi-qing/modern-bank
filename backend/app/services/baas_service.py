"""
Unit-style BaaS simulation: Hold / Move / Spend / Lend.
All balances simulated — no real Fed or card networks.
"""

from __future__ import annotations

import random
import string
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User, Notification
from app.models.baas import (
    DepositAccount, BaasPayment, BaasCard, CreditAccount,
    DepositProduct, AccountStatus, PaymentRail, PaymentDirection,
    PaymentLifecycle, BaasCardKind, BaasCardStatus, CreditAccountStatus,
)
from app.models.baas_schemas import (
    DepositAccountCreate, PaymentCreate, BaasCardCreate, CreditAccountCreate,
)

SIM_ROUTING = "021000021"


def _acct_number(length: int = 10) -> str:
    return "".join(random.choices(string.digits, k=length))


def _last4() -> str:
    return "".join(random.choices(string.digits, k=4))


def create_deposit_account(db: Session, user: User, data: DepositAccountCreate) -> DepositAccount:
    is_wallet = data.deposit_product == DepositProduct.WALLET
    acc = DepositAccount(
        user_id=user.id,
        name=data.name,
        status=AccountStatus.OPEN,
        deposit_product=data.deposit_product,
        routing_number=SIM_ROUTING,
        account_number=_acct_number(12 if is_wallet else 10),
        currency="USD",
        balance=round(data.initial_deposit, 2),
        hold=0.0,
        available=round(data.initial_deposit, 2),
        tags=data.tags or {"purpose": data.deposit_product.value},
        is_wallet=is_wallet,
    )
    db.add(acc)
    db.add(Notification(
        user_id=user.id,
        title="Account opened",
        message=f"{'Wallet' if is_wallet else 'Deposit account'} '{data.name}' is open.",
        type="system",
    ))
    db.commit()
    db.refresh(acc)
    return acc


def list_deposit_accounts(db: Session, user_id: int) -> list[DepositAccount]:
    return (
        db.query(DepositAccount)
        .filter(DepositAccount.user_id == user_id, DepositAccount.status != AccountStatus.CLOSED)
        .order_by(DepositAccount.created_at.desc())
        .all()
    )


def create_payment(db: Session, user: User, data: PaymentCreate) -> BaasPayment:
    acc = db.query(DepositAccount).filter(
        DepositAccount.id == data.account_id, DepositAccount.user_id == user.id
    ).first()
    if not acc or acc.status != AccountStatus.OPEN:
        raise HTTPException(404, "Source account not found or not open")

    if data.idempotency_key:
        existing = db.query(BaasPayment).filter(
            BaasPayment.idempotency_key == data.idempotency_key
        ).first()
        if existing:
            return existing

    if data.rail == PaymentRail.BOOK:
        if not data.counterparty_account_id:
            raise HTTPException(400, "Book payment requires counterparty_account_id")
        cp = db.query(DepositAccount).filter(
            DepositAccount.id == data.counterparty_account_id
        ).first()
        if not cp or cp.status != AccountStatus.OPEN:
            raise HTTPException(404, "Counterparty account not found")
        if acc.available < data.amount:
            raise HTTPException(400, "Insufficient available balance")
        acc.balance = round(acc.balance - data.amount, 2)
        acc.available = round(acc.available - data.amount, 2)
        cp.balance = round(cp.balance + data.amount, 2)
        cp.available = round(cp.available + data.amount, 2)
        status = PaymentLifecycle.COMPLETED
        completed_at = datetime.now(timezone.utc)
        cp_name, cp_routing, cp_account, cp_type = cp.name, cp.routing_number, cp.account_number, "Checking"
    else:
        if data.direction == PaymentDirection.DEBIT or data.rail in (
            PaymentRail.ACH, PaymentRail.WIRE, PaymentRail.RTP, PaymentRail.CHECK, PaymentRail.CROSS_BORDER
        ):
            if acc.available < data.amount and data.direction != PaymentDirection.CREDIT:
                # For outbound debit from our account
                if data.direction == PaymentDirection.DEBIT or True:
                    if acc.available < data.amount:
                        raise HTTPException(400, "Insufficient available balance")
                    acc.balance = round(acc.balance - data.amount, 2)
                    acc.available = round(acc.available - data.amount, 2)
        status = PaymentLifecycle.PENDING if data.rail != PaymentRail.RTP else PaymentLifecycle.SENT
        completed_at = None
        cp_name = data.counterparty.name if data.counterparty else None
        cp_routing = data.counterparty.routing_number if data.counterparty else None
        cp_account = data.counterparty.account_number if data.counterparty else None
        cp_type = data.counterparty.account_type if data.counterparty else None

    pay = BaasPayment(
        user_id=user.id,
        account_id=acc.id,
        rail=data.rail,
        direction=data.direction,
        amount=data.amount,
        currency="USD",
        status=status,
        description=data.description,
        cp_name=cp_name,
        cp_routing=cp_routing,
        cp_account=cp_account,
        cp_account_type=cp_type,
        counterparty_account_id=data.counterparty_account_id,
        same_day=data.same_day,
        idempotency_key=data.idempotency_key,
        completed_at=completed_at,
    )
    db.add(pay)
    db.add(Notification(
        user_id=user.id,
        title=f"Payment {status.value}",
        message=f"{data.rail.value} ${data.amount:.2f} — {status.value}",
        type="transfer",
    ))
    db.commit()
    db.refresh(pay)
    return pay


def list_payments(db: Session, user_id: int, limit: int = 50) -> list[BaasPayment]:
    return (
        db.query(BaasPayment)
        .filter(BaasPayment.user_id == user_id)
        .order_by(BaasPayment.created_at.desc())
        .limit(limit)
        .all()
    )


def create_baas_card(db: Session, user: User, data: BaasCardCreate) -> BaasCard:
    if not data.account_id and not data.credit_account_id:
        raise HTTPException(400, "Provide account_id or credit_account_id")
    last4 = _last4()
    now = datetime.now(timezone.utc)
    card = BaasCard(
        user_id=user.id,
        account_id=data.account_id,
        credit_account_id=data.credit_account_id,
        kind=data.kind,
        status=BaasCardStatus.ACTIVE,
        last_four=last4,
        expiration=f"{now.month:02d}/{now.year + 3}",
        shipping_street=data.shipping_street,
        shipping_city=data.shipping_city,
        shipping_state=data.shipping_state,
        shipping_postal=data.shipping_postal,
        daily_limit=data.daily_limit,
    )
    db.add(card)
    db.add(Notification(
        user_id=user.id,
        title="Card issued",
        message=f"Card •••• {last4} is active.",
        type="card",
    ))
    db.commit()
    db.refresh(card)
    return card


def list_baas_cards(db: Session, user_id: int) -> list[BaasCard]:
    return db.query(BaasCard).filter(BaasCard.user_id == user_id).order_by(BaasCard.created_at.desc()).all()


def freeze_baas_card(db: Session, user: User, card_id: int) -> BaasCard:
    card = db.query(BaasCard).filter(BaasCard.id == card_id, BaasCard.user_id == user.id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    if card.status == BaasCardStatus.ACTIVE:
        card.status = BaasCardStatus.FROZEN
    elif card.status == BaasCardStatus.FROZEN:
        card.status = BaasCardStatus.ACTIVE
    db.commit()
    db.refresh(card)
    return card


def create_credit_account(db: Session, user: User, data: CreditAccountCreate) -> CreditAccount:
    ca = CreditAccount(
        user_id=user.id,
        name=data.name,
        status=CreditAccountStatus.OPEN,
        credit_terms=data.credit_terms,
        currency="USD",
        credit_limit=data.credit_limit,
        balance=0.0,
        hold=0.0,
        available=data.credit_limit,
    )
    db.add(ca)
    db.add(Notification(
        user_id=user.id,
        title="Credit line opened",
        message=f"{data.name} — limit ${data.credit_limit:,.0f}",
        type="system",
    ))
    db.commit()
    db.refresh(ca)
    return ca


def list_credit_accounts(db: Session, user_id: int) -> list[CreditAccount]:
    return (
        db.query(CreditAccount)
        .filter(CreditAccount.user_id == user_id, CreditAccount.status != CreditAccountStatus.CLOSED)
        .all()
    )


def baas_dashboard(db: Session, user_id: int) -> dict:
    deposits = list_deposit_accounts(db, user_id)
    credits = list_credit_accounts(db, user_id)
    cards = list_baas_cards(db, user_id)
    payments = list_payments(db, user_id, 10)
    return {
        "deposit_accounts": deposits,
        "credit_accounts": credits,
        "cards": cards,
        "recent_payments": payments,
        "total_deposits": sum(a.balance for a in deposits),
        "total_credit_available": sum(c.available for c in credits),
    }
