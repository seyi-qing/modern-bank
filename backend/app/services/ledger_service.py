"""Double-entry posting and reconciliation primitives."""
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.ledger import LedgerAccount, LedgerEntry, LedgerEntryDirection, LedgerJournal
from app.models.user import Account

CENT = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT)


def get_or_create_ledger_account(db: Session, account: Account) -> LedgerAccount:
    row = db.query(LedgerAccount).filter(LedgerAccount.account_id == account.id).with_for_update().first()
    if row:
        if row.currency != account.currency:
            raise HTTPException(status_code=409, detail="Ledger/account currency mismatch")
        return row
    row = LedgerAccount(
        account_id=account.id,
        code=f"ACCOUNT:{account.id}",
        currency=account.currency,
        is_system=False,
    )
    db.add(row)
    db.flush()
    return row


def post_transfer(db: Session, *, transaction, source: Account, destination: Account) -> LedgerJournal:
    amount = money(transaction.amount)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be positive")
    if source.currency != destination.currency:
        raise HTTPException(status_code=400, detail="Cross-currency transfers are not supported")
    if source.currency != transaction.currency:
        raise HTTPException(status_code=409, detail="Transaction currency mismatch")
    if money(source.balance) < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    src = get_or_create_ledger_account(db, source)
    dst = get_or_create_ledger_account(db, destination)
    journal = LedgerJournal(
        transaction_id=transaction.id,
        reference=transaction.reference,
        currency=transaction.currency,
        description=transaction.description,
    )
    db.add(journal)
    db.flush()
    db.add_all([
        LedgerEntry(
            journal_id=journal.id,
            ledger_account_id=src.id,
            direction=LedgerEntryDirection.DEBIT,
            amount=amount,
            currency=transaction.currency,
        ),
        LedgerEntry(
            journal_id=journal.id,
            ledger_account_id=dst.id,
            direction=LedgerEntryDirection.CREDIT,
            amount=amount,
            currency=transaction.currency,
        ),
    ])
    source.balance = money(source.balance) - amount
    destination.balance = money(destination.balance) + amount
    db.flush()
    if not journal_is_balanced(db, journal.id):
        raise HTTPException(status_code=500, detail="Ledger invariant violated: journal is not balanced")
    return journal


def journal_is_balanced(db: Session, journal_id: int) -> bool:
    debit = db.query(func.coalesce(func.sum(LedgerEntry.amount), 0)).filter(
        LedgerEntry.journal_id == journal_id,
        LedgerEntry.direction == LedgerEntryDirection.DEBIT,
    ).scalar() or Decimal("0")
    credit = db.query(func.coalesce(func.sum(LedgerEntry.amount), 0)).filter(
        LedgerEntry.journal_id == journal_id,
        LedgerEntry.direction == LedgerEntryDirection.CREDIT,
    ).scalar() or Decimal("0")
    return money(debit) == money(credit)


def reconcile_account(db: Session, account_id: int) -> dict:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    ledger = db.query(LedgerAccount).filter(LedgerAccount.account_id == account_id).first()
    if not ledger:
        book = money(account.balance)
        return {
            "account_id": account_id,
            "currency": account.currency,
            "book_balance": book,
            "ledger_balance": Decimal("0.00"),
            "difference": book,
            "balanced": book == Decimal("0.00"),
        }
    credits = db.query(func.coalesce(func.sum(LedgerEntry.amount), 0)).filter(
        LedgerEntry.ledger_account_id == ledger.id,
        LedgerEntry.direction == LedgerEntryDirection.CREDIT,
    ).scalar() or Decimal("0")
    debits = db.query(func.coalesce(func.sum(LedgerEntry.amount), 0)).filter(
        LedgerEntry.ledger_account_id == ledger.id,
        LedgerEntry.direction == LedgerEntryDirection.DEBIT,
    ).scalar() or Decimal("0")
    ledger_balance = money(credits) - money(debits)
    book = money(account.balance)
    difference = book - ledger_balance
    return {
        "account_id": account_id,
        "currency": account.currency,
        "book_balance": book,
        "ledger_balance": ledger_balance,
        "difference": difference,
        "balanced": difference == Decimal("0.00"),
    }


def reconcile_all_accounts(db: Session) -> dict:
    results = [reconcile_account(db, a.id) for a in db.query(Account).order_by(Account.id).all()]
    failures = [r for r in results if not r["balanced"]]
    return {
        "accounts_checked": len(results),
        "accounts_balanced": len(results) - len(failures),
        "accounts_out_of_balance": len(failures),
        "ok": not failures,
        "results": results,
    }
