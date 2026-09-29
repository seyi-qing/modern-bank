"""Banking Core v2.1 endpoints."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, Transaction
from app.models.schemas import TransactionOut
from app.models.schemas_banking_core_v21 import TransferV21Request
from app.services.banking_core_v21 import transfer_v21

router = APIRouter(prefix="/banking/v2", tags=["Banking Core v2.1"])


@router.post("/transfer", response_model=TransactionOut)
def transfer(
    data: TransferV21Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if idempotency_key:
        data.idempotency_key = idempotency_key
    try:
        result = transfer_v21(db, current_user, data)
        db.commit()
        db.refresh(result)
        return result
    except Exception:
        db.rollback()
        raise


@router.get("/transactions/{transaction_id}", response_model=TransactionOut)
def transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id, Transaction.user_id == current_user.id
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx
