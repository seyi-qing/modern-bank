"""One-shot ops script (Neon / Codespaces).

1) Create staff user ops@modernbank.dev (role=operations) if missing
2) Scale the $1,000,000 book account → $1,000,000,000 with a balanced
   adjustment journal so reconciliation stays ok:true

Does NOT touch Alex (demo@) balances unless that account is the $1M one
(by design: targets account with balance closest to 1_000_000).

Usage (backend/ with DATABASE_URL set):
  python -m scripts.ops_seed_staff_and_scale_balance
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import secrets

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole, Account, AccountType
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
TARGET_BALANCE = Decimal("1000000000.00")  # $1B
NEAR_ONE_MILLION = Decimal("1000000.00")


def ensure_staff(db) -> User:
    user = db.query(User).filter(User.email == STAFF_EMAIL).first()
    if user:
        print(f"Staff user already exists: {STAFF_EMAIL} id={user.id} role={user.role}")
        # ensure role is operations (not customer)
        try:
            from sqlalchemy import text

            db.execute(
                text("UPDATE users SET role = CAST('operations' AS userrole) WHERE id = :id"),
                {"id": user.id},
            )
            db.flush()
            db.refresh(user)
        except Exception as e:
            # try without cast if type name differs
            print(f"  note: role update skipped ({e})")
        return user

    user = User(
        email=STAFF_EMAIL,
        hashed_password=get_password_hash(STAFF_PASSWORD),
        full_name=STAFF_NAME,
        role=UserRole.OPERATIONS,
        is_active=True,
        is_verified=True,
        kyc_status="approved",
    )
    db.add(user)
    db.flush()

    # Optional small checking account so staff can log into customer surfaces if needed
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
    print(f"Created staff {STAFF_EMAIL} / {STAFF_PASSWORD} id={user.id} account={acct_num}")
    return user


def find_one_million_account(db) -> Account | None:
    """Prefer exact 1_000_000.00; else closest active USD account at/above 900k."""
    exact = (
        db.query(Account)
        .filter(Account.balance == NEAR_ONE_MILLION, Account.is_active == True)
        .order_by(Account.id)
        .first()
    )
    if exact:
        return exact
    candidates = (
        db.query(Account)
        .filter(Account.is_active == True, Account.currency == "USD")
        .order_by(Account.id)
        .all()
    )
    for a in candidates:
        if money(a.balance) >= Decimal("900000.00") and money(a.balance) < TARGET_BALANCE:
            return a
    return None


def scale_to_one_billion(db, account: Account) -> None:
    current = money(account.balance)
    if current == TARGET_BALANCE:
        print(f"Account {account.id} already at {TARGET_BALANCE}")
        return
    if current > TARGET_BALANCE:
        raise SystemExit(
            f"Account {account.id} balance {current} is already above $1B; refusing."
        )

    delta = money(TARGET_BALANCE - current)
    ledger = get_or_create_ledger_account(db, account)

    # System opening control (same as opening-balance script)
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
        description=f"Ops scale book+ledger from {current} to {TARGET_BALANCE}",
    )
    db.add(journal)
    db.flush()

    # Double-entry: debit system control, credit customer liability account
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
        raise SystemExit(f"Recon failed after scale: {check}")

    print(
        f"Scaled account {account.id} ({account.account_number}) "
        f"{current} → {TARGET_BALANCE}; journal {ref}; recon OK"
    )


def main():
    db = SessionLocal()
    try:
        ensure_staff(db)

        target = find_one_million_account(db)
        if not target:
            print("No ~$1M account found to scale; staff user step only.")
            db.commit()
            return

        print(
            f"Target account id={target.id} user_id={target.user_id} "
            f"balance={target.balance} number={target.account_number}"
        )
        scale_to_one_billion(db, target)
        db.commit()

        # Final recon summary
        from app.services.ledger_service import reconcile_all_accounts

        summary = reconcile_all_accounts(db)
        print("Recon:", summary["ok"], "balanced", summary["accounts_balanced"], "/", summary["accounts_checked"])
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
