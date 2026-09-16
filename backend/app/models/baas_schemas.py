"""Pydantic schemas for Unit-inspired BaaS resources."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.baas import (
    DepositProduct, AccountStatus, PaymentRail, PaymentDirection,
    PaymentLifecycle, BaasCardKind, BaasCardStatus, CreditAccountStatus,
)


class DepositAccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    deposit_product: DepositProduct = DepositProduct.CHECKING
    tags: Optional[Dict[str, Any]] = None
    initial_deposit: float = Field(0.0, ge=0)


class DepositAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    status: AccountStatus
    deposit_product: DepositProduct
    routing_number: str
    account_number: str
    currency: str
    balance: float
    hold: float
    available: float
    tags: Optional[Dict[str, Any]]
    is_wallet: bool
    created_at: datetime


class CounterpartyIn(BaseModel):
    name: str = Field(..., max_length=50)
    routing_number: str = Field(..., min_length=9, max_length=9)
    account_number: str = Field(..., min_length=4, max_length=17)
    account_type: str = Field("Checking", pattern="^(Checking|Savings)$")


class PaymentCreate(BaseModel):
    account_id: int
    rail: PaymentRail
    direction: PaymentDirection = PaymentDirection.CREDIT
    amount: float = Field(..., gt=0, le=1_000_000)
    description: Optional[str] = Field(None, max_length=50)
    counterparty: Optional[CounterpartyIn] = None
    counterparty_account_id: Optional[int] = None
    same_day: bool = False
    idempotency_key: Optional[str] = Field(None, max_length=64)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_id: int
    rail: PaymentRail
    direction: PaymentDirection
    amount: float
    currency: str
    status: PaymentLifecycle
    description: Optional[str]
    reason: Optional[str]
    cp_name: Optional[str]
    cp_routing: Optional[str]
    cp_account: Optional[str]
    cp_account_type: Optional[str]
    counterparty_account_id: Optional[int]
    same_day: bool
    created_at: datetime
    completed_at: Optional[datetime]


class BaasCardCreate(BaseModel):
    account_id: Optional[int] = None
    credit_account_id: Optional[int] = None
    kind: BaasCardKind = BaasCardKind.VIRTUAL_DEBIT
    shipping_street: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postal: Optional[str] = None
    daily_limit: Optional[float] = Field(None, ge=0)


class BaasCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_id: Optional[int]
    credit_account_id: Optional[int]
    kind: BaasCardKind
    status: BaasCardStatus
    last_four: str
    expiration: str
    shipping_street: Optional[str]
    shipping_city: Optional[str]
    shipping_state: Optional[str]
    shipping_postal: Optional[str]
    shipping_country: str
    daily_limit: Optional[float]
    created_at: datetime


class CreditAccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    credit_terms: str = "standard"
    credit_limit: float = Field(5000.0, gt=0, le=500_000)


class CreditAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    status: CreditAccountStatus
    credit_terms: str
    currency: str
    credit_limit: float
    balance: float
    hold: float
    available: float
    created_at: datetime


class BaasDashboard(BaseModel):
    deposit_accounts: List[DepositAccountOut]
    credit_accounts: List[CreditAccountOut]
    cards: List[BaasCardOut]
    recent_payments: List[PaymentOut]
    total_deposits: float
    total_credit_available: float
