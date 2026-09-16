"""Unit-style BaaS simulation service."""

from __future__ import annotations
import random
import string
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User, Notification
from app.models.baas import (
    DepositAccount, BaasPayment, BaasCard, CreditAccount,
    DepositProduct, AccountStatus, PaymentRail, PaymentDirection,
    PaymentLifecycle, BaasCardKind, BaasCardStatus, CreditAccountStatus,
)
from app.models.baas_schemas import DepositAccountCreate, PaymentCreate, BaasCardCreate, CreditAccountCreate

SIM_ROUTING = "021000021"


def _acct_number(length: int = 10) -> str:
    return "".join(random.choices(string.digits, k=length))


def _last4() -> str:
    return "".join(random.choices(string.digits, k=4))


def create_deposit_account(db: Session, user: User, data: DepositAccountCreate) -> DepositAccount:
    is_wallet = data.deposit_product == DepositProduct.WALLET
    acc = DepositAccount(
        user_id=user.id, name=data.name, status=AccountStatus.OPEN,
        deposit_product=data.deposit_product, routing_number=SIM_ROUTING,
        account_number=_acct_number(12 if is_wallet else 10), currency="USD",
        balance=round(data.initial_deposit, 2), hold=0.0,
        available=round(data.initial_deposit, 2),
        tags=data.tags or {"purpose": data.deposit_product.value}, is_wallet=is_wallet,
    )
    db.add(acc)
    db.add(Notification(user_id=user.id, title="Account opened",
        message=f"{'Wallet' if is_wallet else 'Deposit account'} '{data.name}' is open.", type="system"))
    db.commit()
    db.refresh(acc)
    return acc


def list_deposit_accounts(db: Session, user_id: int) -> list[DepositAccount]:
    return db.query(DepositAccount).filter(
        DepositAccount.user_id == user_id, DepositAccount.status != AccountStatus.CLOSED
    ).order_by(DepositAccount.created_at.desc()).all()


def create_payment(db: Session, user: User, data: PaymentCreate) -> BaasPayment:
    acc = db.query(DepositAccount).filter(DepositAccount.id == data.account_id, DepositAccount.user_id == user.id).first()
    if not acc or acc.status != AccountStatus.OPEN:
        raise HTTPException(404, "Source account not found or not open")
    if data.idempotency_key:
        existing = db.query(BaasPayment).filter(BaasPayment.idempotency_key == data.idempotency_key).first()
        if existing:
            return existing
    if data.rail == PaymentRail.BOOK:
        if not data.counterparty_account_id:
            raise HTTPException(400, "bookPayment requires counterparty_account_id")
        dest = db.query(DepositAccount).filter(DepositAccount.id == data.counterparty_account_id).first()
        if not dest or dest.status != AccountStatus.OPEN:
            raise HTTPException(404, "Counterparty account not found")
        if dest.id == acc.id:
            raise HTTPException(400, "Cannot book to the same account")
    else:
        if not data.counterparty and data.direction == PaymentDirection.CREDIT:
            raise HTTPException(400, f"{data.rail.value} credit requires counterparty")
    if data.direction == PaymentDirection.CREDIT and acc.available < data.amount:
        raise HTTPException(400, "Insufficient available balance")

    payment = BaasPayment(
        user_id=user.id, account_id=acc.id, rail=data.rail, direction=data.direction,
        amount=round(data.amount, 2), currency="USD", status=PaymentLifecycle.PENDING,
        description=data.description, same_day=data.same_day,
        idempotency_key=data.idempotency_key or f"pay-{uuid.uuid4().hex[:16]}",
        counterparty_account_id=data.counterparty_account_id,
    )
    if data.counterparty:
        payment.cp_name = data.counterparty.name
        payment.cp_routing = data.counterparty.routing_number
        payment.cp_account = data.counterparty.account_number
        payment.cp_account_type = data.counterparty.account_type
    db.add(payment)
    db.flush()

    instant = {PaymentRail.BOOK, PaymentRail.RTP, PaymentRail.WIRE}
    if data.rail in instant or (data.rail == PaymentRail.ACH and data.same_day):
        _settle_payment(db, payment, acc)
    else:
        payment.status = PaymentLifecycle.SENT
        if data.direction == PaymentDirection.CREDIT and data.rail != PaymentRail.BOOK:
            acc.balance = round(acc.balance - data.amount, 2)
            acc.available = round(acc.available - data.amount, 2)
        payment.completed_at = datetime.now(timezone.utc)
        payment.status = PaymentLifecycle.COMPLETED

    db.add(Notification(user_id=user.id, title=f"{data.rail.value} {payment.status.value}",
        message=f"${data.amount:.2f} · {data.description or data.rail.value}", type="transfer"))
    db.commit()
    db.refresh(payment)
    return payment


def _settle_payment(db: Session, payment: BaasPayment, source: DepositAccount) -> None:
    if payment.rail == PaymentRail.BOOK and payment.counterparty_account_id:
        dest = db.query(DepositAccount).filter(DepositAccount.id == payment.counterparty_account_id).first()
        if not dest:
            payment.status = PaymentLifecycle.REJECTED
            payment.reason = "Counterparty missing"
            return
        if payment.direction == PaymentDirection.CREDIT:
            source.balance = round(source.balance - payment.amount, 2)
            source.available = round(source.available - payment.amount, 2)
            dest.balance = round(dest.balance + payment.amount, 2)
            dest.available = round(dest.available + payment.amount, 2)
        payment.status = PaymentLifecycle.COMPLETED
        payment.completed_at = datetime.now(timezone.utc)
        return
    if payment.direction == PaymentDirection.CREDIT:
        source.balance = round(source.balance - payment.amount, 2)
        source.available = round(source.available - payment.amount, 2)
    else:
        source.balance = round(source.balance + payment.amount, 2)
        source.available = round(source.available + payment.amount, 2)
    payment.status = PaymentLifecycle.COMPLETED
    payment.completed_at = datetime.now(timezone.utc)


def list_payments(db: Session, user_id: int, limit: int = 50) -> list[BaasPayment]:
    return db.query(BaasPayment).filter(BaasPayment.user_id == user_id).order_by(BaasPayment.created_at.desc()).limit(limit).all()


def create_baas_card(db: Session, user: User, data: BaasCardCreate) -> BaasCard:
    if data.kind in (BaasCardKind.BUSINESS_CREDIT, BaasCardKind.BUSINESS_CHARGE):
        if not data.credit_account_id:
            raise HTTPException(400, "Credit/charge cards require credit_account_id")
        if not db.query(CreditAccount).filter(CreditAccount.id == data.credit_account_id, CreditAccount.user_id == user.id).first():
            raise HTTPException(404, "Credit account not found")
    else:
        if not data.account_id:
            raise HTTPException(400, "Debit cards require account_id")
        if not db.query(DepositAccount).filter(DepositAccount.id == data.account_id, DepositAccount.user_id == user.id).first():
            raise HTTPException(404, "Deposit account not found")
    now = datetime.now(timezone.utc)
    card = BaasCard(
        user_id=user.id, account_id=data.account_id, credit_account_id=data.credit_account_id,
        kind=data.kind, status=BaasCardStatus.ACTIVE, last_four=_last4(),
        expiration=f"{now.month:02d}/{now.year + 3}",
        shipping_street=data.shipping_street, shipping_city=data.shipping_city,
        shipping_state=data.shipping_state, shipping_postal=data.shipping_postal,
        daily_limit=data.daily_limit,
    )
    db.add(card)
    db.add(Notification(user_id=user.id, title="Card issued", message=f"{data.kind.value} ending in {card.last_four} is active.", type="card"))
    db.commit()
    db.refresh(card)
    return card


def list_baas_cards(db: Session, user_id: int) -> list[BaasCard]:
    return db.query(BaasCard).filter(BaasCard.user_id == user_id).order_by(BaasCard.created_at.desc()).all()


def freeze_baas_card(db: Session, user: User, card_id: int) -> BaasCard:
    card = db.query(BaasCard).filter(BaasCard.id == card_id, BaasCard.user_id == user.id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    card.status = BaasCardStatus.FROZEN if card.status == BaasCardStatus.ACTIVE else BaasCardStatus.ACTIVE
    db.commit()
    db.refresh(card)
    return card


def create_credit_account(db: Session, user: User, data: CreditAccountCreate) -> CreditAccount:
    ca = CreditAccount(
        user_id=user.id, name=data.name, status=CreditAccountStatus.OPEN,
        credit_terms=data.credit_terms, currency="USD",
        credit_limit=round(data.credit_limit, 2), balance=0.0, hold=0.0,
        available=round(data.credit_limit, 2),
    )
    db.add(ca)
    db.add(Notification(user_id=user.id, title="Credit line opened",
        message=f"{data.name}: ${data.credit_limit:,.0f} available.", type="system"))
    db.commit()
    db.refresh(ca)
    return ca


def list_credit_accounts(db: Session, user_id: int) -> list[CreditAccount]:
    return db.query(CreditAccount).filter(
        CreditAccount.user_id == user_id, CreditAccount.status != CreditAccountStatus.CLOSED
    ).order_by(CreditAccount.created_at.desc()).all()


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
        "total_deposits": round(sum(a.available for a in deposits), 2),
        "total_credit_available": round(sum(c.available for c in credits), 2),
    }
