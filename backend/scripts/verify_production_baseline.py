"""Read-only production baseline verification.

This script never writes, stamps, migrates, or alters the database.
Run it against a production-derived staging branch before any production
baseline operation.
"""
import os
import sys
from sqlalchemy import create_engine, inspect, text

REQUIRED_TABLES = {
    "users", "accounts", "transactions", "savings_goals", "cards",
    "ledger_accounts", "ledger_journals", "ledger_entries", "audit_logs",
}

def main():
    url = os.getenv("DATABASE_URL", "")
    if not url.startswith(("postgresql://", "postgresql+psycopg2://")):
        raise SystemExit("Refusing to run: PostgreSQL DATABASE_URL required")

    engine = create_engine(url, pool_pre_ping=True)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    missing = REQUIRED_TABLES - tables
    if missing:
        raise SystemExit(f"FAIL: missing required tables: {sorted(missing)}")

    with engine.connect() as conn:
        checks = {
            "idempotency_column": conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_name='transactions' AND column_name='idempotency_key')"
            )).scalar(),
            "ledger_enum": conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname='ledgerentrydirection')"
            )).scalar(),
            "journals_balanced": conn.execute(text(
                "SELECT NOT EXISTS ("
                "SELECT j.id FROM ledger_journals j "
                "LEFT JOIN ledger_entries e ON e.journal_id=j.id "
                "GROUP BY j.id "
                "HAVING COALESCE(SUM(CASE WHEN e.direction='debit' THEN e.amount ELSE 0 END),0) "
                "<> COALESCE(SUM(CASE WHEN e.direction='credit' THEN e.amount ELSE 0 END),0)"
                ")"
            )).scalar(),
            "orphan_customer_ledgers": conn.execute(text(
                "SELECT NOT EXISTS ("
                "SELECT 1 FROM ledger_accounts "
                "WHERE is_system=false AND account_id IS NULL)"
            )).scalar(),
        }

        money_types = conn.execute(text(
            "SELECT table_name, column_name, data_type, numeric_scale "
            "FROM information_schema.columns "
            "WHERE table_name IN ('accounts','transactions','savings_goals','cards') "
            "AND column_name IN ('balance','amount','target_amount','current_amount','spending_limit') "
            "ORDER BY table_name,column_name"
        )).mappings().all()

    failures = [name for name, ok in checks.items() if not ok]
    bad_money = [
        dict(row) for row in money_types
        if row["data_type"] != "numeric" or row["numeric_scale"] != 2
    ]

    if failures or bad_money:
        print("PRODUCTION BASELINE VERIFICATION: FAIL")
        if failures:
            print("Failed checks:", ", ".join(failures))
        if bad_money:
            print("Non-NUMERIC money columns:", bad_money)
        return 1

    print("PRODUCTION BASELINE VERIFICATION: PASS")
    print("All required tables, ledger integrity, idempotency column, and money types verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
