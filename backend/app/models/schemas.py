"""
Pydantic schemas — money fields accept Decimal from Numeric ORM columns.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any, Union
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.models.user import UserRole, AccountType, TransactionType, TransactionStatus, CardType, CardStatus


def _as_float(v: Any) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    kyc_status: str
    created_at: datetime
    last_login: Optional[datetime]

    @field_validator("role", mode="before")
    @classmethod
    def coerce_role(cls, v):
        if isinstance(v, UserRole):
            return v
        if isinstance(v, str):
            # Accept ADMIN / admin / operations / OPERATIONS
            try:
                return UserRole[v]  # name
            except KeyError:
                try:
                    return UserRole(v.lower())  # value
                except ValueError:
                    try:
                        return UserRole[v.upper()]
                    except KeyError:
                        return UserRole.CUSTOMER
        return v


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserOut] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_number: str
    account_type: str
    balance: float
    currency: str
    is_active: bool
    created_at: datetime

    @field_validator("balance", mode="before")
    @classmethod
    def bal(cls, v):
        return _as_float(v)

    @field_validator("account_type", mode="before")
    @classmethod
    def atype(cls, v):
        if hasattr(v, "value"):
            return v.value
        if hasattr(v, "name"):
            return str(v.name).lower()
        return str(v).lower() if v is not None else "checking"


class AccountCreate(BaseModel):
    account_type: AccountType = AccountType.CHECKING
    initial_deposit: float = Field(0.0, ge=0)


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_number: str
    amount: float = Field(..., gt=0, le=50000)
    description: Optional[str] = Field(None, max_length=200)


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_id: int
    amount: float
    currency: str
    type: str
    status: str
    description: Optional[str]
    reference: Optional[str]
    is_flagged: bool
    fraud_score: float
    created_at: datetime

    @field_validator("amount", "fraud_score", mode="before")
    @classmethod
    def money(cls, v):
        return _as_float(v)

    @field_validator("type", "status", mode="before")
    @classmethod
    def enum_str(cls, v):
        if hasattr(v, "value"):
            return v.value
        return str(v).lower() if v is not None else v


class TransactionFilter(BaseModel):
    account_id: Optional[int] = None
    type: Optional[TransactionType] = None
    status: Optional[TransactionStatus] = None
    limit: int = Field(50, ge=1, le=200)


class DashboardSummary(BaseModel):
    total_balance: float
    accounts: List[AccountOut]
    recent_transactions: List[TransactionOut]
    monthly_spending: float
    monthly_income: float
    savings_progress: float

    @field_validator(
        "total_balance", "monthly_spending", "monthly_income", "savings_progress",
        mode="before",
    )
    @classmethod
    def floats(cls, v):
        return _as_float(v)


class AIInsight(BaseModel):
    title: str
    message: str
    category: str
    confidence: float


class SavingsGoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0)
    deadline: Optional[datetime] = None


class SavingsGoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    target_amount: float
    current_amount: float
    deadline: Optional[datetime]
    created_at: datetime

    @field_validator("target_amount", "current_amount", mode="before")
    @classmethod
    def money(cls, v):
        return _as_float(v)


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_accounts: int
    total_balance: float
    transaction_volume_24h: float
    flagged_transactions: int
    new_users_today: int

    @field_validator("total_balance", "transaction_volume_24h", mode="before")
    @classmethod
    def money(cls, v):
        return _as_float(v)


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    kyc_status: Optional[str] = None
    role: Optional[UserRole] = None

    @field_validator("role", mode="before")
    @classmethod
    def coerce_role(cls, v):
        if v is None or isinstance(v, UserRole):
            return v
        if isinstance(v, str):
            try:
                return UserRole[v]
            except KeyError:
                try:
                    return UserRole(v.lower())
                except ValueError:
                    return UserRole[v.upper()]
        return v


class CardCreate(BaseModel):
    account_id: int
    card_type: CardType = CardType.VIRTUAL
    label: Optional[str] = Field(None, max_length=50)
    spending_limit: Optional[float] = Field(None, ge=0)


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_id: int
    card_number_masked: str
    last_four: str
    card_type: str
    status: str
    expiry_month: int
    expiry_year: int
    spending_limit: Optional[float]
    label: Optional[str]
    created_at: datetime
    frozen_at: Optional[datetime]

    @field_validator("spending_limit", mode="before")
    @classmethod
    def lim(cls, v):
        return None if v is None else _as_float(v)

    @field_validator("card_type", "status", mode="before")
    @classmethod
    def enum_str(cls, v):
        if hasattr(v, "value"):
            return v.value
        return str(v).lower() if v is not None else v


class CardUpdate(BaseModel):
    status: Optional[CardStatus] = None
    spending_limit: Optional[float] = Field(None, ge=0)
    label: Optional[str] = Field(None, max_length=50)


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    message: str
    is_read: bool
    type: str
    created_at: datetime
