"""ModernBank Banking Core v2.1: idempotent atomic transfers and admin review."""
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User, Account, Transaction, TransactionType, TransactionStatus, Notification
from app.models.schemas_banking_core_v21 import TransferV21Request
from app.services.fraud_engine import FraudEngine
from app.services.ledger_service import post_transfer, money
from app.core.config import settings


def _existing_idempotent(db: Session, user_id: int, key: str):
    return db.query(Transaction).filter(
        Transaction.user_id == user_id, Transaction.idempotency_key == key
    ).first()


def _assert_idempotency_match(tx: Transaction, data: TransferV21Request, destination_id: int | None = None):
    if (
        tx.account_id != data.from_account_id
        or tx.counterparty_account_id is None
        or (destination_id is not None and tx.counterparty_account_id != destination_id)
        or tx.currency != data.currency
        or money(tx.amount) != money(data.amount)
        or (tx.description or "") != (data.description or "")
    ):
        raise HTTPException(
            status_code=409,
            detail="Idempotency key was already used for a different transfer",
        )


def _lock_transfer_accounts(db: Session, source_id: int, destination_number: str):
    """Lock both rows in deterministic primary-key order to reduce deadlocks."""
    destination_probe = db.query(Account.id).filter(
        Account.account_number == destination_number,
        Account.is_active == True,
    ).first()
    if not destination_probe:
        raise HTTPException(status_code=404, detail="Destination account not found")

    ids = sorted({source_id, destination_probe[0]})
    rows = (
        db.query(Account)
        .filter(Account.id.in_(ids))
        .order_by(Account.id.asc())
        .with_for_update()
        .all()
    )
    by_id = {row.id: row for row in rows}
    return by_id.get(source_id), by_id.get(destination_probe[0])


def _return_existing(tx: Transaction, data: TransferV21Request, destination_id: int | None = None):
    _assert_idempotency_match(tx, data, destination_id)
    return tx


def transfer_v21(db: Session, user: User, data: TransferV21Request) -> Transaction:
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if data.amount > Decimal(str(settings.MAX_TRANSFER_AMOUNT)):
        raise HTTPException(status_code=400, detail="Amount exceeds transfer limit")
    data.currency = data.currency.upper()

    existing = _existing_idempotent(db, user.id, data.idempotency_key)
    if existing:
        return _return_existing(existing, data)

    source, destination = _lock_transfer_accounts(db, data.from_account_id, data.to_account_number)
    if not source or not source.is_active or source.user_id != user.id:
        raise HTTPException(status_code=404, detail="Source account not found")
    if not destination or not destination.is_active:
        raise HTTPException(status_code=404, detail="Destination account not found")
    if destination.id == source.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    existing = _existing_idempotent(db, user.id, data.idempotency_key)
    if existing:
        return _return_existing(existing, data, destination.id)

    if source.currency != data.currency or destination.currency != data.currency:
        raise HTTPException(status_code=400, detail="Currency mismatch")
    if money(source.balance) < money(data.amount):
        raise HTTPException(status_code=400, detail="Insufficient funds")

    fraud = FraudEngine(db).score_transfer(user, float(data.amount), source, destination)
    tx = Transaction(
        user_id=user.id,
        account_id=source.id,
        counterparty_account_id=destination.id,
        amount=money(data.amount),
        currency=data.currency,
        type=TransactionType.TRANSFER_OUT,
        status=TransactionStatus.FLAGGED if fraud.is_flagged else TransactionStatus.COMPLETED,
        description=data.description or f"Transfer to {destination.account_number[-4:]}",
        reference=f"TXN-{uuid4().hex[:12].upper()}",
        idempotency_key=data.idempotency_key,
        is_flagged=fraud.is_flagged,
        fraud_score=fraud.score,
    )
    db.add(tx)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = _existing_idempotent(db, user.id, data.idempotency_key)
        if existing:
            return _return_existing(existing, data)
        raise

    if fraud.is_flagged:
        db.add(Notification(
            user_id=user.id,
            title="Transfer under review",
            message=f"Transfer {tx.reference} is under review. Reason: {'; '.join(fraud.reasons) or 'risk policy'}",
            type="fraud",
        ))
        return tx

    post_transfer(db, transaction=tx, source=source, destination=destination)
    db.add(Transaction(
        user_id=destination.user_id,
        account_id=destination.id,
        counterparty_account_id=source.id,
        amount=money(data.amount),
        currency=data.currency,
        type=TransactionType.TRANSFER_IN,
        status=TransactionStatus.COMPLETED,
        description=f"Transfer from {source.account_number[-4:]}",
        reference=f"{tx.reference}-IN",
        is_flagged=False,
        fraud_score=0.0,
    ))
    db.add(Notification(
        user_id=destination.user_id,
        title="Money received",
        message=f"You received {data.amount:.2f} {data.currency} from {user.full_name}. Ref: {tx.reference}",
        type="transfer",
    ))
    return tx


def admin_review_transfer(db: Session, transaction_id: int, action: str, reason: str, admin: User) -> Transaction:
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).with_for_update().first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.type != TransactionType.TRANSFER_OUT or not tx.is_flagged:
        raise HTTPException(status_code=400, detail="Only flagged transfers can be reviewed")
    if tx.status not in (TransactionStatus.FLAGGED, TransactionStatus.PENDING):
        raise HTTPException(status_code=409, detail="Transaction is already final")

    if action == "reject":
        tx.status = TransactionStatus.FAILED
        tx.is_flagged = True
        db.add(Notification(
            user_id=tx.user_id,
            title="Transfer rejected",
            message=f"Transfer {tx.reference} was rejected: {reason}",
            type="fraud",
        ))
        return tx

    if not tx.counterparty_account_id:
        raise HTTPException(status_code=409, detail="Flagged transfer has no destination account")
    dest_number = db.query(Account.account_number).filter(Account.id == tx.counterparty_account_id).scalar()
    source, destination = _lock_transfer_accounts(db, tx.account_id, dest_number)
    if not source or not destination or not source.is_active or not destination.is_active:
        raise HTTPException(status_code=409, detail="Transfer accounts are unavailable")
    if money(source.balance) < money(tx.amount):
        raise HTTPException(status_code=400, detail="Insufficient funds to approve transfer")

    tx.status = TransactionStatus.COMPLETED
    tx.is_flagged = False
    post_transfer(db, transaction=tx, source=source, destination=destination)
    db.add(Transaction(
        user_id=destination.user_id,
        account_id=destination.id,
        counterparty_account_id=source.id,
        amount=money(tx.amount),
        currency=tx.currency,
        type=TransactionType.TRANSFER_IN,
        status=TransactionStatus.COMPLETED,
        description=f"Reviewed transfer from {source.account_number[-4:]}",
        reference=f"{tx.reference}-IN",
        is_flagged=False,
        fraud_score=0.0,
    ))
    db.add(Notification(
        user_id=destination.user_id,
        title="Money received",
        message=f"A reviewed transfer of {tx.amount:.2f} {tx.currency} has been completed. Ref: {tx.reference}",
        type="transfer",
    ))
    return tx
