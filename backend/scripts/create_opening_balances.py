"""Create controlled opening-balance journals for existing ModernBank accounts.

Run ONCE after 0004_ledger_system_accounts and after independently verifying
all pre-v2.1 Account.balance values. Refuses to run if opening journals exist.

From backend/:  python -m scripts.create_opening_balances
"""
from decimal import Decimal
from app.core.database import SessionLocal
from app.models.user import Account
from app.models.ledger import LedgerAccount, LedgerJournal, LedgerEntry, LedgerEntryDirection

CONTROL_PREFIX = "SYSTEM:OPENING:"


def money(v):
    return Decimal(str(v)).quantize(Decimal("0.01"))


def main():
    db = SessionLocal()
    try:
        if db.query(LedgerJournal).filter(LedgerJournal.reference.like("OPENING-%")).count():
            raise SystemExit("Opening-balance journals already exist; refusing to run again.")

        accounts = (
            db.query(Account)
            .filter(Account.is_active == True)
            .order_by(Account.id)
            .with_for_update()
            .all()
        )
        if not accounts:
            print("No active customer accounts found; nothing to open.")
            return

        currencies = sorted({a.currency.upper() for a in accounts})
        controls = {}
        for currency in currencies:
            code = f"{CONTROL_PREFIX}{currency}"
            control = db.query(LedgerAccount).filter(LedgerAccount.code == code).with_for_update().first()
            if not control:
                control = LedgerAccount(code=code, account_id=None, currency=currency, is_system=True)
                db.add(control)
                db.flush()
            controls[currency] = control

        created = 0
        for account in accounts:
            amount = money(account.balance)
            ledger = db.query(LedgerAccount).filter(LedgerAccount.account_id == account.id).first()
            if ledger:
                raise SystemExit(
                    f"Ledger account already exists for account {account.id}; aborting to avoid partial opening."
                )
            ledger = LedgerAccount(
                account_id=account.id,
                code=f"ACCOUNT:{account.id}",
                currency=account.currency.upper(),
                is_system=False,
            )
            db.add(ledger)
            db.flush()
            if amount == 0:
                continue
            ref = f"OPENING-{account.currency.upper()}-{account.id}"
            journal = LedgerJournal(
                transaction_id=None,
                reference=ref,
                currency=account.currency.upper(),
                description="Verified pre-v2.1 opening balance",
            )
            db.add(journal)
            db.flush()
            db.add_all([
                LedgerEntry(
                    journal_id=journal.id,
                    ledger_account_id=controls[account.currency.upper()].id,
                    direction=LedgerEntryDirection.DEBIT,
                    amount=amount,
                    currency=account.currency.upper(),
                ),
                LedgerEntry(
                    journal_id=journal.id,
                    ledger_account_id=ledger.id,
                    direction=LedgerEntryDirection.CREDIT,
                    amount=amount,
                    currency=account.currency.upper(),
                ),
            ])
            created += 1

        db.commit()
        print(
            f"Opening balances created for {created} non-zero account(s); "
            "zero-balance accounts were ledger-backed without journal entries."
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
