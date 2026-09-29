"""Repair the verified legacy production schema for Banking Core v2.1.

This revision is separate from 0003/0004 because production was created by
SQLAlchemy create_all() and already contains the v2.1 ledger schema.

It performs only the missing monetary type conversions and refuses to run
when the expected existing ledger schema or integrity checks are absent.
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_production_schema_repair"
down_revision = "0006_production_baseline"
branch_labels = ("production_baseline",)
depends_on = None

_MONEY_COLUMNS = (
    ("accounts", "balance"),
    ("transactions", "amount"),
    ("savings_goals", "target_amount"),
    ("savings_goals", "current_amount"),
    ("cards", "spending_limit"),
)


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    required = {
        "users",
        "accounts",
        "transactions",
        "savings_goals",
        "cards",
        "ledger_accounts",
        "ledger_journals",
        "ledger_entries",
        "audit_logs",
    }
    missing = sorted(required - tables)
    _require(not missing, f"Production schema repair refused; missing tables: {missing}")

    tx_columns = {c["name"] for c in inspector.get_columns("transactions")}
    _require(
        "idempotency_key" in tx_columns,
        "Production schema repair refused; transactions.idempotency_key is missing",
    )

    ledger_account_columns = {c["name"] for c in inspector.get_columns("ledger_accounts")}
    _require(
        {"code", "is_system", "account_id"}.issubset(ledger_account_columns),
        "Production schema repair refused; ledger_accounts is not at the expected v2.1+ shape",
    )

    unbalanced = bind.execute(sa.text("""
        SELECT count(*)
        FROM (
            SELECT lj.id
            FROM ledger_journals lj
            JOIN ledger_entries le ON le.journal_id = lj.id
            GROUP BY lj.id
            HAVING COALESCE(SUM(CASE WHEN le.direction = 'DEBIT' THEN le.amount ELSE 0 END), 0)
                <> COALESCE(SUM(CASE WHEN le.direction = 'CREDIT' THEN le.amount ELSE 0 END), 0)
        ) q
    """)).scalar_one()
    _require(
        unbalanced == 0,
        f"Production schema repair refused; {unbalanced} ledger journals are unbalanced",
    )

    orphaned = bind.execute(sa.text("""
        SELECT count(*)
        FROM ledger_accounts la
        LEFT JOIN accounts a ON a.id = la.account_id
        WHERE la.is_system = false AND a.id IS NULL
    """)).scalar_one()
    _require(
        orphaned == 0,
        f"Production schema repair refused; {orphaned} orphan customer ledger accounts found",
    )

    for table, column in _MONEY_COLUMNS:
        current_type = bind.execute(
            sa.text("""
                SELECT data_type
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = :table_name
                  AND column_name = :column_name
            """),
            {"table_name": table, "column_name": column},
        ).scalar_one_or_none()

        _require(
            current_type is not None,
            f"Production schema repair refused; {table}.{column} is missing",
        )

        if current_type in ("double precision", "real"):
            bind.execute(
                sa.text(
                    f"ALTER TABLE {table} "
                    f"ALTER COLUMN {column} TYPE NUMERIC(18,2) "
                    f"USING {column}::numeric(18,2)"
                )
            )
        elif current_type != "numeric":
            raise RuntimeError(
                f"Production schema repair refused; unexpected type "
                f"{table}.{column}={current_type!r}"
            )

    enum_labels = [
        row[0]
        for row in bind.execute(sa.text("""
            SELECT e.enumlabel
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'ledgerentrydirection'
            ORDER BY e.enumsortorder
        """)).all()
    ]
    _require(
        enum_labels == ["DEBIT", "CREDIT"],
        "Production schema repair refused; ledgerentrydirection enum is not the expected application enum",
    )


def downgrade():
    raise RuntimeError(
        "Production schema repair is intentionally irreversible; "
        "restore from a verified database backup instead."
    )
