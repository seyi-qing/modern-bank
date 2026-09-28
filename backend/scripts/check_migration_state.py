"""Read-only database migration state diagnostic for ModernBank.

This script NEVER runs Alembic, stamps revisions, creates tables, alters data,
or commits anything. It only inspects the connected database schema.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

# Allow: python backend/scripts/check_migration_state.py
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect, text

from app.core.database import engine


LEGACY_TABLES = {
    "users",
    "accounts",
    "transactions",
    "notifications",
    "savings_goals",
    "cards",
}

LEDGER_TABLES = {
    "ledger_accounts",
    "ledger_journals",
    "ledger_entries",
}

EXPECTED_REVISIONS = {
    "0003_banking_core_v21",
    "0004_ledger_system_accounts",
}


def _table_names(inspector) -> set[str]:
    return set(inspector.get_table_names())


def _columns(inspector, table_name: str) -> set[str]:
    if table_name not in _table_names(inspector):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _current_alembic_revision(connection, tables: set[str]) -> str | None:
    if "alembic_version" not in tables:
        return None
    try:
        return connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar()
    except Exception as exc:  # diagnostic must report, not mutate
        return f"<unreadable: {exc.__class__.__name__}>"


def classify(
    tables: set[str],
    transaction_columns: set[str],
    ledger_account_columns: set[str],
    alembic_revision: str | None,
) -> str:
    legacy_present = {"users", "accounts", "transactions"}.issubset(tables)
    ledger_present = LEDGER_TABLES.issubset(tables)
    idempotency_present = "idempotency_key" in transaction_columns
    system_account_stage = {"code", "is_system"}.issubset(ledger_account_columns)

    if not legacy_present and not ledger_present:
        return "EMPTY_OR_FRESH"

    if legacy_present and not ledger_present and not idempotency_present:
        return "LEGACY_CREATE_ALL_BASELINE"

    if legacy_present and ledger_present and idempotency_present and system_account_stage:
        if alembic_revision == "0004_ledger_system_accounts":
            return "BANKING_CORE_V21_PLUS_0004"
        return "BANKING_CORE_V21_LEDGER_SYSTEM_STAGE"

    if legacy_present and ledger_present and idempotency_present:
        if alembic_revision == "0003_banking_core_v21":
            return "BANKING_CORE_V21_0003"
        return "BANKING_CORE_V21_UNSTAMPED_OR_UNKNOWN_REVISION"

    return "UNKNOWN_OR_PARTIAL_SCHEMA"


def _print_set(label: str, values: Iterable[str]) -> None:
    print(f"{label}: {', '.join(sorted(values)) or '(none)'}")


def main() -> int:
    inspector = inspect(engine)
    tables = _table_names(inspector)
    transaction_columns = _columns(inspector, "transactions")
    ledger_account_columns = _columns(inspector, "ledger_accounts")

    with engine.connect() as connection:
        alembic_revision = _current_alembic_revision(connection, tables)

    state = classify(
        tables,
        transaction_columns,
        ledger_account_columns,
        alembic_revision,
    )

    print("ModernBank migration state (READ ONLY)")
    print("=" * 44)
    print(f"Database dialect: {engine.dialect.name}")
    print(f"State: {state}")
    print(f"Alembic revision: {alembic_revision or '(none)'}")
    print()
    _print_set("Legacy tables present", LEGACY_TABLES & tables)
    _print_set("Ledger tables present", LEDGER_TABLES & tables)
    _print_set("Transaction columns", transaction_columns)
    _print_set("Ledger-account columns", ledger_account_columns)
    print()
    print("Expected upgrade chain:")
    print("  legacy SQLAlchemy create_all schema")
    print("    -> 0003_banking_core_v21")
    print("    -> 0004_ledger_system_accounts")
    print()
    print("NO migration, stamp, create, alter, drop, or commit was performed.")

    if alembic_revision and alembic_revision not in EXPECTED_REVISIONS:
        print(
            "WARNING: alembic_version contains a revision outside the known "
            "ModernBank v2.1 chain."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
