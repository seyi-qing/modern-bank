"""
Core banking logic. Dashboard/stats cast Decimal → float for JSON.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, text
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


def _f(v) -> float:
    if v is None:
        return 0.0
    return float(v)


def get_user_accounts(db: Session, user_id: int) -> list[Account]:
    return db.query(Account).filter(Account.user_id == user_id, Account.is_active == True).all()


def get_account_by_number(db: Session, account_number: str) -> Account | None:
    return db.query(Account).filter(Account.account_number == account_number, Account.is_active == True).first()


def get_dashboard(db: Session, user: User) -> dict:
    accounts = get_user_accounts(db, user.id)
    total_balance = sum((_f(a.balance) for a in accounts), 0.0)
    recent = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )
    thirty_days = datetime.now(timezone.utc) - timedelta(days=30)
    spending = db.execute(
        text(
            """
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE user_id = :uid AND created_at >= :since
              AND type::text IN ('transfer_out','TRANSFER_OUT','payment','PAYMENT','withdrawal','WITHDRAWAL')
              AND status::text IN ('completed','COMPLETED')
            """
        ),
        {"uid": user.id, "since": thirty_days},
    ).scalar()
    income = db.execute(
        text(
            """
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE user_id = :uid AND created_at >= :since
              AND type::text IN ('transfer_in','TRANSFER_IN','deposit','DEPOSIT','interest','INTEREST')
              AND status::text IN ('completed','COMPLETED')
            """
        ),
        {"uid": user.id, "since": thirty_days},
    ).scalar()
    goals = db.query(SavingsGoal).filter(SavingsGoal.user_id == user.id).all()
    progress = (
        sum(_f(g.current_amount) / _f(g.target_amount) for g in goals if _f(g.target_amount) > 0) / len(goals) * 100
        if goals
        else 0.0
    )
    return {
        "total_balance": round(total_balance, 2),
        "accounts": accounts,
        "recent_transactions": recent,
        "monthly_spending": round(_f(spending), 2),
        "monthly_income": round(_f(income), 2),
        "savings_progress": round(progress, 1),
    }


def generate_ai_insights(db: Session, user: User) -> list[AIInsight]:
    accounts = get_user_accounts(db, user.id)
    total = sum((_f(a.balance) for a in accounts), 0.0)
    insights: list[AIInsight] = []
    if total < 500:
        insights.append(
            AIInsight(
                title="Build your emergency fund",
                message="Your balance is under $500. Consider setting aside $50/week into savings.",
                category="savings",
                confidence=0.82,
            )
        )
    elif total > 5000:
        insights.append(
            AIInsight(
                title="Idle cash opportunity",
                message=f"You have ${total:,.0f} available. Consider high-yield savings.",
                category="investment",
                confidence=0.75,
            )
        )
    if not insights:
        insights.append(
            AIInsight(
                title="You're on track",
                message="Your spending patterns look healthy this month.",
                category="general",
                confidence=0.9,
            )
        )
    return insights


def get_admin_stats(db: Session) -> dict:
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    total_accounts = db.query(func.count(Account.id)).scalar() or 0
    total_balance = db.query(func.coalesce(func.sum(Account.balance), 0)).scalar() or 0
    one_day = datetime.now(timezone.utc) - timedelta(days=1)
    volume = db.execute(
        text(
            """
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE created_at >= :since
              AND status::text IN ('completed','COMPLETED')
            """
        ),
        {"since": one_day},
    ).scalar() or 0
    flagged = db.query(func.count(Transaction.id)).filter(Transaction.is_flagged == True).scalar() or 0
    new_today = db.query(func.count(User.id)).filter(User.created_at >= one_day).scalar() or 0
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_accounts": total_accounts,
        "total_balance": round(_f(total_balance), 2),
        "transaction_volume_24h": round(_f(volume), 2),
        "flagged_transactions": flagged,
        "new_users_today": new_today,
    }


def _generate_card_number() -> tuple[str, str]:
    last4 = "".join(random.choices("0123456789", k=4))
    return f"•••• •••• •••• {last4}", last4


def create_card(db: Session, user: User, data: CardCreate) -> Card:
    acc = (
        db.query(Account)
        .filter(Account.id == data.account_id, Account.user_id == user.id, Account.is_active == True)
        .first()
    )
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    active_count = (
        db.query(func.count(Card.id))
        .filter(Card.user_id == user.id, Card.status != "cancelled")
        .scalar()
        or 0
    )
    if active_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 cards reached")
    masked, last4 = _generate_card_number()
    now = datetime.now(timezone.utc)
    ct = data.card_type.value if hasattr(data.card_type, "value") else str(data.card_type)
    card = Card(
        user_id=user.id,
        account_id=acc.id,
        card_number_masked=masked,
        last_four=last4,
        card_type=ct,
        status="active",
        expiry_month=now.month,
        expiry_year=now.year + 3,
        spending_limit=data.spending_limit,
        label=data.label or ("Virtual" if ct == "virtual" else "Physical"),
    )
    db.add(card)
    db.add(
        Notification(
            user_id=user.id,
            title="New card issued",
            message=f"Your {ct} card ending in {last4} is ready.",
            type="card",
        )
    )
    db.commit()
    db.refresh(card)
    return card


def list_cards(db: Session, user_id: int) -> list[Card]:
    return db.query(Card).filter(Card.user_id == user_id).order_by(Card.created_at.desc()).all()


def update_card(
    db: Session,
    user: User,
    card_id: int,
    status: CardStatus | str | None = None,
    spending_limit: float | None = None,
    label: str | None = None,
) -> Card:
    card = db.query(Card).filter(Card.id == card_id, Card.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if status is not None:
        st = status.value if hasattr(status, "value") else str(status)
        card.status = st
        if st == "frozen":
            card.frozen_at = datetime.now(timezone.utc)
        elif st == "active":
            card.frozen_at = None
    if spending_limit is not None:
        card.spending_limit = spending_limit
    if label is not None:
        card.label = label
    db.commit()
    db.refresh(card)
    return card


def list_notifications(db: Session, user_id: int, limit: int = 30) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def mark_notifications_read(db: Session, user_id: int, ids: list[int] | None = None):
    q = db.query(Notification).filter(
        Notification.user_id == user_id, Notification.is_read == False
    )
    if ids:
        q = q.filter(Notification.id.in_(ids))
    q.update({"is_read": True})
    db.commit()
