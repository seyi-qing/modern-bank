"""Schemas for card requests and customer 360."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.user import CardType, AccountType, UserRole
from app.models.card_request import CardRequestStatus


class CardRequestCreate(BaseModel):
    account_id: int
    card_type: CardType = CardType.VIRTUAL
    label: Optional[str] = Field(None, max_length=50)
    spending_limit: Optional[Decimal] = Field(None, ge=0)


class CardRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    account_id: int
    card_type: CardType
    label: Optional[str]
    spending_limit: Optional[Decimal]
    status: CardRequestStatus
    review_reason: Optional[str]
    issued_card_id: Optional[int]
    created_at: datetime
    reviewed_at: Optional[datetime]


class CardRequestReview(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: str = Field(..., min_length=3, max_length=500)


class CustomerAccountBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_number: str
    account_type: AccountType
    balance: Decimal
    currency: str
    is_active: bool


class CustomerCardBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    last_four: str
    card_type: str
    status: str
    label: Optional[str]


class Customer360(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    kyc_status: str
    created_at: datetime
    last_login: Optional[datetime]
    accounts: List[CustomerAccountBrief]
    cards: List[CustomerCardBrief]
    recent_transactions: List[dict]
    open_card_requests: int
