"""
Customer banking endpoints: accounts, transfers, dashboard, insights, goals.
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, Transaction, SavingsGoal
from app.models.schemas import (
    AccountOut, TransferRequest, TransactionOut, DashboardSummary,
    AIInsight, SavingsGoalCreate, SavingsGoalOut, UserUpdate, UserOut
)
from app.services.banking_service import (
    get_user_accounts, transfer_funds, get_dashboard, generate_ai_insights
)

router = APIRouter(prefix="/banking", tags=["Banking"])


@router.get("/accounts", response_model=List[AccountOut])
def list_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_accounts(db, current_user.id)


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_dashboard(db, current_user)


@router.post("/transfer", response_model=TransactionOut)
def transfer(
    data: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transfer_funds(db, current_user, data)


@router.get("/transactions", response_model=List[TransactionOut])
def list_transactions(
    account_id: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if account_id:
        q = q.filter(Transaction.account_id == account_id)
    return q.order_by(Transaction.created_at.desc()).limit(limit).all()


@router.get("/insights", response_model=List[AIInsight])
def insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return generate_ai_insights(db, current_user)


@router.get("/goals", response_model=List[SavingsGoalOut])
def list_goals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SavingsGoal).filter(SavingsGoal.user_id == current_user.id).all()


@router.post("/goals", response_model=SavingsGoalOut, status_code=201)
def create_goal(
    data: SavingsGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = SavingsGoal(
        user_id=current_user.id,
        name=data.name,
        target_amount=data.target_amount,
        deadline=data.deadline,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.patch("/profile", response_model=UserOut)
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.phone is not None:
        current_user.phone = data.phone
    db.commit()
    db.refresh(current_user)
    return current_user
