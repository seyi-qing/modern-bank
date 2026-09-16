"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole, AccountType, TransactionType, TransactionStatus, CardType, CardStatus


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None


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


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_number: str
    account_type: AccountType
    balance: float
    currency: str
    is_active: bool
    created_at: datetime


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
    type: TransactionType
    status: TransactionStatus
    description: Optional[str]
    reference: Optional[str]
    is_flagged: bool
    fraud_score: float
    created_at: datetime


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


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_accounts: int
    total_balance: float
    transaction_volume_24h: float
    flagged_transactions: int
    new_users_today: int


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    kyc_status: Optional[str] = None
    role: Optional[UserRole] = None


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
    card_type: CardType
    status: CardStatus
    expiry_month: int
    expiry_year: int
    spending_limit: Optional[float]
    label: Optional[str]
    created_at: datetime
    frozen_at: Optional[datetime]


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
