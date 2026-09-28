"""Double-entry ledger models for ModernBank Banking Core v2.1."""
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Integer, Numeric, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class LedgerEntryDirection(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class LedgerJournal(Base):
    __tablename__ = "ledger_journals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), unique=True, nullable=True, index=True)
    reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    entries: Mapped[list["LedgerEntry"]] = relationship("LedgerEntry", back_populates="journal", cascade="all, delete-orphan")


class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Customer ledger accounts point to Account. System/control accounts are null.
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), unique=True, nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    entries: Mapped[list["LedgerEntry"]] = relationship("LedgerEntry", back_populates="ledger_account")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    journal_id: Mapped[int] = mapped_column(ForeignKey("ledger_journals.id"), nullable=False, index=True)
    ledger_account_id: Mapped[int] = mapped_column(ForeignKey("ledger_accounts.id"), nullable=False, index=True)
    direction: Mapped[LedgerEntryDirection] = mapped_column(SAEnum(LedgerEntryDirection), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    journal: Mapped["LedgerJournal"] = relationship("LedgerJournal", back_populates="entries")
    ledger_account: Mapped["LedgerAccount"] = relationship("LedgerAccount", back_populates="entries")
    __table_args__ = (Index("ix_ledger_entries_journal_direction", "journal_id", "direction"),)
