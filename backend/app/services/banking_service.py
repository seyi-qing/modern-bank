"""
Core banking logic: transfers, balance updates, fraud scoring, cards, insights.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models.user import (
    User, Account, Transaction, TransactionType, TransactionStatus,
    Notification, SavingsGoal, Card, CardType, CardStatus
)
from app.models.schemas import TransferRequest, AIInsight, CardCreate
from app.core.config import settings
from app.services.fraud_engine import FraudEngine
import uuid
import random


def get_user_accounts(db: Session, user_id: int) -> list[Account]:
    return db.query(Account).filter(Account.user_id == user_id, Account.is_active == True).all()


def get_account_by_number(db: Session, account_number: str) -> Account | None:
    return db.query(Account).filter(Account.account_number == account_number, Account.is_active == True).first()


def transfer_funds(db: Session, user: User, data: TransferRequest) -> Transaction:
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if data.amount > settings.MAX_TRANSFER_AMOUNT:
        raise HTTPException(status_code=400, detail=f"Amount exceeds maximum of {settings.MAX_TRANSFER_AMOUNT}")

    from_acc = db.query(Account).filter(
        Account.id == data.from_account_id, Account.user_id == user.id, Account.is_active == True
    ).first()
    if not from_acc:
        raise HTTPException(status_code=404, detail="Source account not found")
    if from_acc.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    to_acc = get_account_by_number(db, data.to_account_number)
    if not to_acc:
        raise HTTPException(status_code=404, detail="Destination account not found. Only internal accounts supported in demo.")
    if to_acc.id == from_acc.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    engine = FraudEngine(db)
    fraud = engine.score_transfer(user, data.amount, from_acc, to_acc)

    ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    reason_str = "; ".join(fraud.reasons) if fraud.reasons else None
    out_tx = Transaction(
        user_id=user.id,
        account_id=from_acc.id,
        counterparty_account_id=to_acc.id,
        amount=data.amount,
        currency=from_acc.currency,
        type=TransactionType.TRANSFER_OUT,
        status=TransactionStatus.FLAGGED if fraud.is_flagged else TransactionStatus.COMPLETED,
        description=data.description or f"Transfer to {to_acc.account_number[-4:]}",
        reference=ref,
        is_flagged=fraud.is_flagged,
        fraud_score=fraud.score,
    )
    db.add(out_tx)

    if not fraud.is_flagged:
        from_acc.balance = round(from_acc.balance - data.amount, 2)
        to_acc.balance = round(to_acc.balance + data.amount, 2)
        db.add(Transaction(
            user_id=to_acc.user_id,
            account_id=to_acc.id,
            counterparty_account_id=from_acc.id,
            amount=data.amount,
            currency=to_acc.currency,
            type=TransactionType.TRANSFER_IN,
            status=TransactionStatus.COMPLETED,
            description=f"Transfer from {from_acc.account_number[-4:]}",
            reference=ref,
            is_flagged=False,
            fraud_score=0.0,
        ))
        db.add(Notification(
            user_id=to_acc.user_id,
            title="Money received",
            message=f"You received ${data.amount:.2f} from {user.full_name}. Ref: {ref}",
            type="transfer",
        ))
    else:
        db.add(Notification(
            user_id=user.id,
            title="Transfer under review",
            message=f"Your transfer of ${data.amount:.2f} was flagged ({reason_str}). Ref: {ref}",
            type="fraud",
        ))

    db.commit()
    db.refresh(out_tx)

    try:
        import asyncio
        from app.services.ws_manager import manager
        payload = {
            "type": "notification",
            "title": "Transfer flagged" if fraud.is_flagged else "Transfer completed",
            "message": f"${data.amount:.2f} • Ref {ref}",
            "fraud_score": fraud.score,
            "flagged": fraud.is_flagged,
        }
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(manager.send_personal(user.id, payload))
            if not fraud.is_flagged:
                asyncio.create_task(manager.send_personal(to_acc.user_id, {
                    "type": "notification",
                    "title": "Money received",
                    "message": f"${data.amount:.2f} from {user.full_name}",
                }))
    except Exception:
        pass

    return out_tx


def get_dashboard(db: Session, user: User) -> dict:
    accounts = get_user_accounts(db, user.id)
    total_balance = sum(a.balance for a in accounts)
    recent = (
        db.query(Transaction).filter(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc()).limit(10).all()
    )
    thirty_days = datetime.now(timezone.utc) - timedelta(days=30)
    spending = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(
        Transaction.user_id == user.id,
        Transaction.created_at >= thirty_days,
        Transaction.type.in_([TransactionType.TRANSFER_OUT, TransactionType.PAYMENT, TransactionType.WITHDRAWAL]),
        Transaction.status == TransactionStatus.COMPLETED,
    ).scalar()
    income = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(
        Transaction.user_id == user.id,
        Transaction.created_at >= thirty_days,
        Transaction.type.in_([TransactionType.TRANSFER_IN, TransactionType.DEPOSIT, TransactionType.INTEREST]),
        Transaction.status == TransactionStatus.COMPLETED,
    ).scalar()
    goals = db.query(SavingsGoal).filter(SavingsGoal.user_id == user.id).all()
    progress = (
        sum(g.current_amount / g.target_amount for g in goals if g.target_amount > 0) / len(goals) * 100
        if goals else 0.0
    )
    return {
        "total_balance": round(total_balance, 2),
        "accounts": accounts,
        "recent_transactions": recent,
        "monthly_spending": round(float(spending), 2),
        "monthly_income": round(float(income), 2),
        "savings_progress": round(progress, 1),
    }


def generate_ai_insights(db: Session, user: User) -> list[AIInsight]:
    accounts = get_user_accounts(db, user.id)
    total = sum(a.balance for a in accounts)
    insights: list[AIInsight] = []
    if total < 500:
        insights.append(AIInsight(
            title="Build your emergency fund",
            message="Your balance is under $500. Consider setting aside $50/week into savings.",
            category="savings", confidence=0.82,
        ))
    elif total > 5000:
        insights.append(AIInsight(
            title="Idle cash opportunity",
            message=f"You have ${total:,.0f} available. Consider high-yield savings.",
            category="opportunity", confidence=0.75,
        ))
    thirty_days = datetime.now(timezone.utc) - timedelta(days=30)
    spending = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(
        Transaction.user_id == user.id,
        Transaction.created_at >= thirty_days,
        Transaction.type == TransactionType.TRANSFER_OUT,
    ).scalar() or 0
    if spending > 2000:
        insights.append(AIInsight(
            title="High monthly outflow",
            message=f"You moved ${spending:,.0f} out in the last 30 days.",
            category="spending", confidence=0.68,
        ))
    if not insights:
        insights.append(AIInsight(
            title="You're on track",
            message="Your spending patterns look healthy this month.",
            category="opportunity", confidence=0.9,
        ))
    return insights


def get_admin_stats(db: Session) -> dict:
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    total_accounts = db.query(func.count(Account.id)).scalar() or 0
    total_balance = db.query(func.coalesce(func.sum(Account.balance), 0.0)).scalar() or 0.0
    one_day = datetime.now(timezone.utc) - timedelta(days=1)
    volume = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(
        Transaction.created_at >= one_day, Transaction.status == TransactionStatus.COMPLETED
    ).scalar() or 0
    flagged = db.query(func.count(Transaction.id)).filter(Transaction.is_flagged == True).scalar() or 0
    new_today = db.query(func.count(User.id)).filter(User.created_at >= one_day).scalar() or 0
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_accounts": total_accounts,
        "total_balance": round(float(total_balance), 2),
        "transaction_volume_24h": round(float(volume), 2),
        "flagged_transactions": flagged,
        "new_users_today": new_today,
    }


def _generate_card_number() -> tuple[str, str]:
    last4 = "".join(random.choices("0123456789", k=4))
    return f"•••• •••• •••• {last4}", last4


def create_card(db: Session, user: User, data: CardCreate) -> Card:
    acc = db.query(Account).filter(Account.id == data.account_id, Account.user_id == user.id, Account.is_active == True).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    active_count = db.query(func.count(Card.id)).filter(Card.user_id == user.id, Card.status != CardStatus.CANCELLED).scalar() or 0
    if active_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 cards reached")
    masked, last4 = _generate_card_number()
    now = datetime.now(timezone.utc)
    card = Card(
        user_id=user.id,
        account_id=acc.id,
        card_number_masked=masked,
        last_four=last4,
        card_type=data.card_type,
        status=CardStatus.ACTIVE,
        expiry_month=now.month,
        expiry_year=now.year + 3,
        spending_limit=data.spending_limit,
        label=data.label or ("Virtual" if data.card_type == CardType.VIRTUAL else "Physical"),
    )
    db.add(card)
    db.add(Notification(user_id=user.id, title="New card issued", message=f"Your {data.card_type.value} card ending in {last4} is ready.", type="card"))
    db.commit()
    db.refresh(card)
    return card


def list_cards(db: Session, user_id: int) -> list[Card]:
    return db.query(Card).filter(Card.user_id == user_id).order_by(Card.created_at.desc()).all()


def update_card(db: Session, user: User, card_id: int, status: CardStatus | None = None, spending_limit: float | None = None, label: str | None = None) -> Card:
    card = db.query(Card).filter(Card.id == card_id, Card.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if status is not None:
        if status == CardStatus.FROZEN and card.status == CardStatus.ACTIVE:
            card.status = CardStatus.FROZEN
            card.frozen_at = datetime.now(timezone.utc)
            db.add(Notification(user_id=user.id, title="Card frozen", message=f"Card ending in {card.last_four} has been frozen.", type="card"))
        elif status == CardStatus.ACTIVE and card.status == CardStatus.FROZEN:
            card.status = CardStatus.ACTIVE
            card.frozen_at = None
            db.add(Notification(user_id=user.id, title="Card unfrozen", message=f"Card ending in {card.last_four} is active again.", type="card"))
        elif status == CardStatus.CANCELLED:
            card.status = CardStatus.CANCELLED
            db.add(Notification(user_id=user.id, title="Card cancelled", message=f"Card ending in {card.last_four} has been cancelled.", type="card"))
        else:
            card.status = status
    if spending_limit is not None:
        card.spending_limit = spending_limit
    if label is not None:
        card.label = label
    db.commit()
    db.refresh(card)
    return card


def list_notifications(db: Session, user_id: int, limit: int = 30) -> list[Notification]:
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).limit(limit).all()


def mark_notifications_read(db: Session, user_id: int, ids: list[int] | None = None):
    q = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False)
    if ids:
        q = q.filter(Notification.id.in_(ids))
    q.update({"is_read": True})
    db.commit()
