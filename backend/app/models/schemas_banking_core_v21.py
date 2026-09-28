"""Additional v2.1 schemas for ledger transfers and admin ops."""
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TransferV21Request(BaseModel):
    from_account_id: int
    to_account_number: str = Field(..., min_length=6, max_length=20)
    amount: Decimal = Field(..., gt=Decimal("0.00"), le=Decimal("50000.00"))
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: Optional[str] = Field(None, max_length=200)
    idempotency_key: str = Field(..., min_length=16, max_length=255)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.upper()


class AdminTransactionAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: str = Field(..., min_length=5, max_length=500)


class ReconciliationResult(BaseModel):
    account_id: int
    currency: str
    book_balance: Decimal
    ledger_balance: Decimal
    difference: Decimal
    balanced: bool


class ReconciliationSummary(BaseModel):
    accounts_checked: int
    accounts_balanced: int
    accounts_out_of_balance: int
    ok: bool
    results: list[ReconciliationResult]
