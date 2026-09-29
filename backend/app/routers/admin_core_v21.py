"""Admin operational endpoints for Banking Core v2.1."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User, Transaction
from app.models.schemas import TransactionOut
from app.models.schemas_banking_core_v21 import (
    AdminTransactionAction,
    ReconciliationResult,
    ReconciliationSummary,
)
from app.services.banking_core_v21 import admin_review_transfer
from app.services.ledger_service import reconcile_account, reconcile_all_accounts
from app.services.audit import write_audit

router = APIRouter(prefix="/admin/core", tags=["Admin Banking Core"])


@router.post("/transactions/{transaction_id}/review", response_model=TransactionOut)
def review(
    transaction_id: int,
    data: AdminTransactionAction,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    before = {"status": tx.status.value, "is_flagged": tx.is_flagged}
    try:
        result = admin_review_transfer(db, transaction_id, data.action, data.reason, admin)
        after = {"status": result.status.value, "is_flagged": result.is_flagged}
        write_audit(
            db,
            actor=admin,
            action="ADMIN_REVIEW_TRANSFER",
            resource_type="transaction",
            resource_id=result.id,
            reason=data.reason,
            before=before,
            after=after,
            request=request,
        )
        db.commit()
        db.refresh(result)
        return result
    except Exception:
        db.rollback()
        raise


@router.get("/reconciliation", response_model=ReconciliationSummary)
def reconciliation(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return reconcile_all_accounts(db)


@router.get("/reconciliation/{account_id}", response_model=ReconciliationResult)
def account_reconciliation(
    account_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return reconcile_account(db, account_id)
