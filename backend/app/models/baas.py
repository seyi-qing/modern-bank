"""
Unit-inspired BaaS resource models (simulation).
"""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import enum


class DepositProduct(str, enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    WALLET = "wallet"


class AccountStatus(str, enum.Enum):
    OPEN = "Open"
    FROZEN = "Frozen"
    CLOSED = "Closed"


class PaymentRail(str, enum.Enum):
    ACH = "achPayment"
    BOOK = "bookPayment"
    WIRE = "wirePayment"
    RTP = "rtpPayment"
    CHECK = "checkPayment"
    CROSS_BORDER = "crossBorderPayment"


class PaymentDirection(str, enum.Enum):
    CREDIT = "Credit"
    DEBIT = "Debit"


class PaymentLifecycle(str, enum.Enum):
    PENDING = "Pending"
    PENDING_REVIEW = "PendingReview"
    SENT = "Sent"
    COMPLETED = "Completed"
    RETURNED = "Returned"
    CANCELED = "Canceled"
    REJECTED = "Rejected"


class BaasCardKind(str, enum.Enum):
    VIRTUAL_DEBIT = "individualVirtualDebitCard"
    PHYSICAL_DEBIT = "individualDebitCard"
    BUSINESS_VIRTUAL_DEBIT = "businessVirtualDebitCard"
    BUSINESS_CHARGE = "businessVirtualChargeCard"
    BUSINESS_CREDIT = "businessCreditCard"


class BaasCardStatus(str, enum.Enum):
    ACTIVE = "Active"
    FROZEN = "Frozen"
    STOLEN = "Stolen"
    LOST = "Lost"
    CLOSED = "Closed"
    INACTIVE = "Inactive"


class CreditAccountStatus(str, enum.Enum):
    OPEN = "Open"
    FROZEN = "Frozen"
    CLOSED = "Closed"


class DepositAccount(Base):
    __tablename__ = "baas_deposit_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[AccountStatus] = mapped_column(SAEnum(AccountStatus), default=AccountStatus.OPEN)
    deposit_product: Mapped[DepositProduct] = mapped_column(SAEnum(DepositProduct), default=DepositProduct.CHECKING)
    routing_number: Mapped[str] = mapped_column(String(9), nullable=False)
    account_number: Mapped[str] = mapped_column(String(17), unique=True, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    hold: Mapped[float] = mapped_column(Float, default=0.0)
    available: Mapped[float] = mapped_column(Float, default=0.0)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_wallet: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class BaasPayment(Base):
    __tablename__ = "baas_payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("baas_deposit_accounts.id"), nullable=False)
    rail: Mapped[PaymentRail] = mapped_column(SAEnum(PaymentRail), nullable=False)
    direction: Mapped[PaymentDirection] = mapped_column(SAEnum(PaymentDirection), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[PaymentLifecycle] = mapped_column(SAEnum(PaymentLifecycle), default=PaymentLifecycle.PENDING)
    description: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cp_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cp_routing: Mapped[str | None] = mapped_column(String(9), nullable=True)
    cp_account: Mapped[str | None] = mapped_column(String(17), nullable=True)
    cp_account_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    counterparty_account_id: Mapped[int | None] = mapped_column(ForeignKey("baas_deposit_accounts.id"), nullable=True)
    same_day: Mapped[bool] = mapped_column(Boolean, default=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BaasCard(Base):
    __tablename__ = "baas_cards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("baas_deposit_accounts.id"), nullable=True)
    credit_account_id: Mapped[int | None] = mapped_column(ForeignKey("baas_credit_accounts.id"), nullable=True)
    kind: Mapped[BaasCardKind] = mapped_column(SAEnum(BaasCardKind), nullable=False)
    status: Mapped[BaasCardStatus] = mapped_column(SAEnum(BaasCardStatus), default=BaasCardStatus.ACTIVE)
    last_four: Mapped[str] = mapped_column(String(4), nullable=False)
    expiration: Mapped[str] = mapped_column(String(7), nullable=False)
    shipping_street: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    shipping_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    shipping_postal: Mapped[str | None] = mapped_column(String(12), nullable=True)
    shipping_country: Mapped[str] = mapped_column(String(2), default="US")
    daily_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CreditAccount(Base):
    __tablename__ = "baas_credit_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[CreditAccountStatus] = mapped_column(SAEnum(CreditAccountStatus), default=CreditAccountStatus.OPEN)
    credit_terms: Mapped[str] = mapped_column(String(50), default="standard")
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    credit_limit: Mapped[float] = mapped_column(Float, default=5000.0)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    hold: Mapped[float] = mapped_column(Float, default=0.0)
    available: Mapped[float] = mapped_column(Float, default=5000.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
