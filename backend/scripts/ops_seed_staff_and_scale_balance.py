"""Ops script — safe, two independent steps.

A) Scale ~$1M account → $1B (balanced ledger journal) — does not create users
B) Create ops@modernbank.dev via ORM (same path as registration), then set role

Usage:
  export DATABASE_URL="postgresql://…?sslmode=require"
  python -m scripts.ops_seed_staff_and_scale_balance
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import secrets
import traceback

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, Account, AccountType, UserRole
from app.models.ledger import (
    LedgerAccount,
    LedgerJournal,
    LedgerEntry,
    LedgerEntryDirection,
)
from app.services.ledger_service import money, reconcile_account, get_or_create_ledger_account

STAFF_EMAIL = "ops@modernbank.dev"
STAFF_PASSWORD = "Staff123!"
STAFF_NAME = "Ops Analyst"
TARGET_BALANCE = Decimal("1000000000.00")
NEAR_ONE_MILLION = Decimal("1000000.00")


def find_one_million_account(db: Session) -> Account | None:
    exact = (
        db.query(Account)
        .filter(Account.balance == NEAR_ONE_MILLION, Account.is_active == True)
        .order_by(Account.id)
        .first()
    )
    if exact:
        return exact
    for a in (
        db.query(Account)
        .filter(Account.is_active == True, Account.currency == "USD")
        .order_by(Account.id)
    ):
        bal = money(a.balance)
        if bal >= Decimal("900000.00") and bal < TARGET_BALANCE:
            return a
    return None


def scale_to_one_billion(db: Session, account: Account) -> None:
    current = money(account.balance)
    if current == TARGET_BALANCE:
        print(f"[scale] Account {account.id} already at {TARGET_BALANCE}")
        return
    if current > TARGET_BALANCE:
        raise SystemExit(f"[scale] Account {account.id} is {current} > $1B; refusing.")

    delta = money(TARGET_BALANCE - current)
    ledger = get_or_create_ledger_account(db, account)

    control_code = f"SYSTEM:OPENING:{account.currency.upper()}"
    control = (
        db.query(LedgerAccount)
        .filter(LedgerAccount.code == control_code)
        .with_for_update()
        .first()
    )
    if not control:
        control = LedgerAccount(
            code=control_code,
            account_id=None,
            currency=account.currency.upper(),
            is_system=True,
        )
        db.add(control)
        db.flush()

    ref = f"ADJ-SCALE-1B-{account.id}-{int(datetime.now(timezone.utc).timestamp())}"
    journal = LedgerJournal(
        transaction_id=None,
        reference=ref,
        currency=account.currency.upper(),
        description=f"Ops scale from {current} to {TARGET_BALANCE}",
    )
    db.add(journal)
    db.flush()
    db.add_all(
        [
            LedgerEntry(
                journal_id=journal.id,
                ledger_account_id=control.id,
                direction=LedgerEntryDirection.DEBIT,
                amount=delta,
                currency=account.currency.upper(),
            ),
            LedgerEntry(
                journal_id=journal.id,
                ledger_account_id=ledger.id,
                direction=LedgerEntryDirection.CREDIT,
                amount=delta,
                currency=account.currency.upper(),
            ),
        ]
    )
    account.balance = TARGET_BALANCE
    db.flush()

    check = reconcile_account(db, account.id)
    if not check["balanced"]:
        raise SystemExit(f"[scale] Recon failed: {check}")

    print(
        f"[scale] Account {account.id} ({account.account_number}) "
        f"{current} → {TARGET_BALANCE}; journal={ref}; recon OK"
    )


def ensure_staff(db: Session) -> None:
    existing = db.query(User).filter(User.email == STAFF_EMAIL).first()
    if existing:
        print(f"[staff] Already exists id={existing.id} role={existing.role}")
        _try_set_operations_role(db, existing.id)
        if not existing.accounts:
            _add_zero_checking(db, existing)
        return

    # Create as CUSTOMER first (enum value known to work in this DB), then promote
    user = User(
        email=STAFF_EMAIL,
        hashed_password=get_password_hash(STAFF_PASSWORD),
        full_name=STAFF_NAME,
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        kyc_status="approved",
    )
    db.add(user)
    db.flush()
    _add_zero_checking(db, user)
    db.flush()
    _try_set_operations_role(db, user.id)
    print(f"[staff] Created {STAFF_EMAIL} / {STAFF_PASSWORD} id={user.id}")


def _add_zero_checking(db: Session, user: User) -> Account:
    acct_num = f"2{secrets.randbelow(10**9):09d}"[:12]
    while db.query(Account).filter(Account.account_number == acct_num).first():
        acct_num = f"2{secrets.randbelow(10**9):09d}"[:12]
    acc = Account(
        user_id=user.id,
        account_number=acct_num,
        account_type=AccountType.CHECKING,
        balance=Decimal("0.00"),
        currency="USD",
        is_active=True,
    )
    db.add(acc)
    db.flush()
    get_or_create_ledger_account(db, acc)
    print(f"[staff] Checking account {acct_num} for user {user.id}")
    return acc


def _try_set_operations_role(db: Session, user_id: int) -> None:
    """Promote to operations using whatever label Postgres actually has."""
    # Discover real enum labels for users.role
    labels = [
        r[0]
        for r in db.execute(
            text(
                """
                SELECT e.enumlabel
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                JOIN pg_attribute a ON a.atttypid = t.oid
                JOIN pg_class c ON c.oid = a.attrelid
                WHERE c.relname = 'users' AND a.attname = 'role' AND NOT a.attisdropped
                """
            )
        ).fetchall()
    ]
    # Prefer lowercase operations, then OPERATIONS, then any containing 'operation'
    candidates = []
    for lab in labels:
        if lab.lower() == "operations":
            candidates.insert(0, lab)
        elif "operation" in lab.lower():
            candidates.append(lab)
    if not candidates:
        print(f"[staff] No operations label in enum {labels}; leaving as customer")
        print("         Run: ALTER TYPE <userrole> ADD VALUE IF NOT EXISTS 'operations';")
        return

    label = candidates[0]
    typ = db.execute(
        text(
            """
            SELECT t.typname FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            JOIN pg_type t ON t.oid = a.atttypid
            WHERE c.relname = 'users' AND a.attname = 'role' AND NOT a.attisdropped
            """
        )
    ).scalar()
    try:
        db.execute(
            text(f"UPDATE users SET role = CAST(:lab AS {typ}) WHERE id = :id"),
            {"lab": label, "id": user_id},
        )
        db.flush()
        print(f"[staff] Role set to {label!r} (type {typ})")
    except Exception as e:
        print(f"[staff] Role update failed (user still customer): {e}")


def main():
    db = SessionLocal()
    try:
        # --- Step A: scale (independent) ---
        target = find_one_million_account(db)
        if not target:
            print("[scale] No ~$1M account found — skip")
        else:
            print(
                f"[scale] Target id={target.id} user_id={target.user_id} "
                f"bal={target.balance} num={target.account_number}"
            )
            scale_to_one_billion(db, target)
        db.commit()
        print("[scale] committed")

        # --- Step B: staff (independent session state) ---
        try:
            ensure_staff(db)
            db.commit()
            print("[staff] committed")
        except Exception:
            db.rollback()
            print("[staff] FAILED — scale was already committed; system balances OK")
            traceback.print_exc()

        from app.services.ledger_service import reconcile_all_accounts

        summary = reconcile_all_accounts(db)
        print(
            "[recon]",
            summary["ok"],
            f"{summary['accounts_balanced']}/{summary['accounts_checked']} balanced",
        )
        for r in summary["results"]:
            print(
                f"  account {r['account_id']}: book={r['book_balance']} "
                f"ledger={r['ledger_balance']} ok={r['balanced']}"
            )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
