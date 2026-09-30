"""One-shot ops script (Neon / Codespaces).

1) Create staff user ops@modernbank.dev (role=operations) if missing
2) Scale the ~$1,000,000 account → $1,000,000,000 with balanced journal

Usage:
  export DATABASE_URL="postgresql://…?sslmode=require"
  python -m scripts.ops_seed_staff_and_scale_balance
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import secrets

from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import Account
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


def _enum_type(db, table: str, column: str) -> str:
    row = db.execute(
        text(
            """
            SELECT t.typname
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            JOIN pg_type t ON t.oid = a.atttypid
            WHERE c.relname = :table AND a.attname = :col AND NOT a.attisdropped
            """
        ),
        {"table": table, "col": column},
    ).first()
    return row[0] if row else column


def ensure_staff(db) -> int:
    row = db.execute(
        text("SELECT id, email, role::text FROM users WHERE email = :e"),
        {"e": STAFF_EMAIL},
    ).first()
    if row:
        print(f"Staff exists: {row[1]} id={row[0]} role={row[2]}")
        role_t = _enum_type(db, "users", "role")
        try:
            db.execute(
                text(f"UPDATE users SET role = CAST('operations' AS {role_t}) WHERE id = :id"),
                {"id": row[0]},
            )
            db.flush()
        except Exception as e:
            print(f"  role note: {e}")
        # Ensure at least one account
        has_acc = db.execute(
            text("SELECT id FROM accounts WHERE user_id = :id LIMIT 1"),
            {"id": row[0]},
        ).first()
        if has_acc:
            return int(row[0])
        user_id = int(row[0])
    else:
        role_t = _enum_type(db, "users", "role")
        hashed = get_password_hash(STAFF_PASSWORD)
        user_id = int(
            db.execute(
                text(
                    f"""
                    INSERT INTO users (
                        email, hashed_password, full_name, phone, role,
                        is_active, is_verified, kyc_status, created_at, last_login
                    ) VALUES (
                        :email, :hp, :name, NULL, CAST('operations' AS {role_t}),
                        true, true, 'approved', NOW(), NULL
                    )
                    RETURNING id
                    """
                ),
                {"email": STAFF_EMAIL, "hp": hashed, "name": STAFF_NAME},
            ).scalar()
        )
        print(f"Created user {STAFF_EMAIL} id={user_id}")

    acct_t = _enum_type(db, "accounts", "account_type")
    acct_num = f"2{secrets.randbelow(10**9):09d}"[:12]
    while db.execute(
        text("SELECT 1 FROM accounts WHERE account_number = :n"), {"n": acct_num}
    ).first():
        acct_num = f"2{secrets.randbelow(10**9):09d}"[:12]

    acc_id = int(
        db.execute(
            text(
                f"""
                INSERT INTO accounts (
                    user_id, account_number, account_type, balance, currency, is_active, created_at
                ) VALUES (
                    :uid, :num, CAST('checking' AS {acct_t}), 0.00, 'USD', true, NOW()
                )
                RETURNING id
                """
            ),
            {"uid": user_id, "num": acct_num},
        ).scalar()
    )

    acc = db.query(Account).filter(Account.id == acc_id).first()
    if acc:
        get_or_create_ledger_account(db, acc)

    print(f"Staff {STAFF_EMAIL} / {STAFF_PASSWORD} id={user_id} account={acct_num}")
    return user_id


def find_one_million_account(db) -> Account | None:
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
        if money(a.balance) >= Decimal("900000.00") and money(a.balance) < TARGET_BALANCE:
            return a
    return None


def scale_to_one_billion(db, account: Account) -> None:
    current = money(account.balance)
    if current == TARGET_BALANCE:
        print(f"Account {account.id} already at {TARGET_BALANCE}")
        return
    if current > TARGET_BALANCE:
        raise SystemExit(f"Account {account.id} balance {current} already above $1B; refusing.")

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
        description=f"Ops scale book+ledger from {current} to {TARGET_BALANCE}",
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
            print("No ~$1M account found to scale; staff step only.")
            db.commit()
            return

        print(
            f"Target account id={target.id} user_id={target.user_id} "
            f"balance={target.balance} number={target.account_number}"
        )
        scale_to_one_billion(db, target)
        db.commit()

        from app.services.ledger_service import reconcile_all_accounts

        summary = reconcile_all_accounts(db)
        print(
            "Recon:",
            summary["ok"],
            "balanced",
            summary["accounts_balanced"],
            "/",
            summary["accounts_checked"],
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
