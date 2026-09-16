"""
Sophisticated (still heuristic) fraud scoring engine.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import Transaction, TransactionType, TransactionStatus, User, Account
from dataclasses import dataclass, field
from typing import List
import random


@dataclass
class FraudResult:
    score: float
    reasons: List[str] = field(default_factory=list)
    is_flagged: bool = False

    def to_dict(self):
        return {
            "score": round(self.score, 3),
            "reasons": self.reasons,
            "is_flagged": self.is_flagged,
        }


class FraudEngine:
    FLAG_THRESHOLD = 0.65

    def __init__(self, db: Session):
        self.db = db

    def score_transfer(
        self,
        user: User,
        amount: float,
        from_account: Account,
        to_account: Account | None = None,
    ) -> FraudResult:
        score = 0.0
        reasons: List[str] = []

        if from_account.balance > 0:
            ratio = amount / from_account.balance
            if ratio >= 0.9:
                score += 0.30
                reasons.append("Near-full balance drain")
            elif ratio >= 0.5:
                score += 0.15
                reasons.append("Large portion of balance")

        if amount >= 25000:
            score += 0.35
            reasons.append("Very high absolute amount")
        elif amount >= 10000:
            score += 0.20
            reasons.append("High absolute amount")
        elif amount >= 5000:
            score += 0.10
            reasons.append("Elevated amount")

        now = datetime.now(timezone.utc)
        one_hour = now - timedelta(hours=1)
        one_day = now - timedelta(days=1)

        count_1h = (
            self.db.query(func.count(Transaction.id))
            .filter(
                Transaction.user_id == user.id,
                Transaction.created_at >= one_hour,
                Transaction.type.in_([TransactionType.TRANSFER_OUT, TransactionType.PAYMENT, TransactionType.CARD_PAYMENT]),
            )
            .scalar()
            or 0
        )
        if count_1h >= 5:
            score += 0.40
            reasons.append(f"High velocity: {count_1h} transfers in last hour")
        elif count_1h >= 3:
            score += 0.22
            reasons.append(f"Elevated velocity: {count_1h} transfers in last hour")

        volume_24h = (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
            .filter(
                Transaction.user_id == user.id,
                Transaction.created_at >= one_day,
                Transaction.type.in_([TransactionType.TRANSFER_OUT, TransactionType.PAYMENT]),
                Transaction.status == TransactionStatus.COMPLETED,
            )
            .scalar()
            or 0.0
        )
        if volume_24h + amount > 50000:
            score += 0.25
            reasons.append("24h volume limit approach")

        account_age_days = (now - from_account.created_at.replace(tzinfo=timezone.utc)).days if from_account.created_at.tzinfo is None else (now - from_account.created_at).days
        if account_age_days < 1:
            score += 0.25
            reasons.append("Brand-new account")
        elif account_age_days < 7:
            score += 0.12
            reasons.append("Young account (<7 days)")

        hour = now.hour
        if hour < 5 or hour >= 23:
            score += 0.08
            reasons.append("Off-hours transfer")

        if to_account:
            prior = (
                self.db.query(func.count(Transaction.id))
                .filter(
                    Transaction.user_id == user.id,
                    Transaction.counterparty_account_id == to_account.id,
                    Transaction.type == TransactionType.TRANSFER_OUT,
                )
                .scalar()
                or 0
            )
            if prior == 0 and amount > 1000:
                score += 0.12
                reasons.append("First large transfer to this recipient")

        score += random.uniform(0.0, 0.05)
        score = min(score, 1.0)
        flagged = score >= self.FLAG_THRESHOLD
        if flagged and not reasons:
            reasons.append("Composite risk score exceeded threshold")

        return FraudResult(score=score, reasons=reasons, is_flagged=flagged)
