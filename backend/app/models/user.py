"""
User and related models.

IMPORTANT: Neon already stores userrole labels as enum NAMES for legacy rows:
  ADMIN, CUSTOMER
and some newer rows as values: operations

We map UserRole by **name** so ADMIN/CUSTOMER keep working.
Staff roles must be written as OPERATIONS, RISK_ANALYST, etc. (names).
"""

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Text,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


def _enum_names(enum_cls):
    """Postgres labels match Python enum member names (ADMIN, CUSTOMER, …)."""
    return [member.name for member in enum_cls]


def _enum_values(enum_cls):
    return [member.value for member in enum_cls]


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    OPERATIONS = "operations"
    RISK_ANALYST = "risk_analyst"
    FINANCE = "finance"
    CARD_OPERATIONS = "card_operations"
    COMPLIANCE = "compliance"
    AUDITOR = "auditor"


class AccountType(str, enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"


class TransactionType(str, enum.Enum):
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"
    FEE = "fee"
    INTEREST = "interest"
    CARD_PAYMENT = "card_payment"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    FLAGGED = "flagged"


class CardStatus(str, enum.Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CANCELLED = "cancelled"
    PENDING = "pending"


class CardType(str, enum.Enum):
    VIRTUAL = "virtual"
    PHYSICAL = "physical"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # name= matches existing PG type; values_callable=names matches ADMIN/CUSTOMER rows
    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="userrole",
            values_callable=_enum_names,
            validate_strings=True,
            create_constraint=False,
            native_enum=True,
        ),
        default=UserRole.CUSTOMER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    kyc_status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    accounts: Mapped[list["Account"]] = relationship(
        "Account", back_populates="owner", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="Transaction.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    cards: Mapped[list["Card"]] = relationship(
        "Card", back_populates="owner", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    account_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    account_type: Mapped[AccountType] = mapped_column(
        SAEnum(
            AccountType,
            name="accounttype",
            values_callable=_enum_values,
            validate_strings=True,
            create_constraint=False,
            native_enum=True,
        ),
        default=AccountType.CHECKING,
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    owner: Mapped["User"] = relationship("User", back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="Transaction.account_id",
        back_populates="account",
    )
    cards: Mapped[list["Card"]] = relationship("Card", back_populates="account")

    def __repr__(self) -> str:
        return f"<Account {self.account_number} bal={self.balance}>"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_transactions_user_idempotency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    counterparty_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    type: Mapped[TransactionType] = mapped_column(
        SAEnum(
            TransactionType,
            values_callable=_enum_values,
            validate_strings=True,
            create_constraint=False,
        ),
        nullable=False,
    )
    status: Mapped[TransactionStatus] = mapped_column(
        SAEnum(
            TransactionStatus,
            values_callable=_enum_values,
            validate_strings=True,
            create_constraint=False,
        ),
        default=TransactionStatus.COMPLETED,
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    fraud_score: Mapped[float] = mapped_column(Numeric(8, 4), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="transactions"
    )
    account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[account_id], back_populates="transactions"
    )

    def __repr__(self) -> str:
        return f"<Tx {self.id} {self.type} {self.amount}>"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    type: Mapped[str] = mapped_column(String(50), default="info")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="notifications")


class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    card_number_masked: Mapped[str] = mapped_column(String(20), nullable=False)
    last_four: Mapped[str] = mapped_column(String(4), nullable=False)
    card_type: Mapped[CardType] = mapped_column(
        SAEnum(
            CardType,
            name="cardtype",
            values_callable=_enum_values,
            validate_strings=True,
            create_constraint=False,
        ),
        default=CardType.VIRTUAL,
    )
    status: Mapped[CardStatus] = mapped_column(
        SAEnum(
            CardStatus,
            name="cardstatus",
            values_callable=_enum_values,
            validate_strings=True,
            create_constraint=False,
        ),
        default=CardStatus.ACTIVE,
    )
    expiry_month: Mapped[int] = mapped_column(Integer, nullable=False)
    expiry_year: Mapped[int] = mapped_column(Integer, nullable=False)
    spending_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship("User", back_populates="cards")
    account: Mapped["Account"] = relationship("Account", back_populates="cards")

    def __repr__(self) -> str:
        return f"<Card {self.last_four} {self.status}>"
