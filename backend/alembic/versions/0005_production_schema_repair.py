"""Repair a verified legacy production schema.

This revision is the production repair step after the database has been
explicitly baselined. It is not a clean-install foundation migration.
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_production_schema_repair"
down_revision = "0004_ledger_system_accounts"
branch_labels = None
depends_on = None


def _has_column(inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    required = {
        "accounts", "transactions", "savings_goals", "cards",
        "ledger_accounts", "ledger_journals", "ledger_entries",
    }
    missing = required - set(inspector.get_table_names())
    if missing:
        raise RuntimeError(
            "Production repair requires the verified existing Banking Core "
            f"schema; missing: {', '.join(sorted(missing))}"
        )

    if not _has_column(inspector, "transactions", "idempotency_key"):
        op.add_column(
            "transactions",
            sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        )

    op.execute(sa.text(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_transactions_idempotency_key "
        "ON transactions (idempotency_key) "
        "WHERE idempotency_key IS NOT NULL"
    ))

    for table, column, nullable in (
        ("accounts", "balance", False),
        ("transactions", "amount", False),
        ("savings_goals", "target_amount", False),
        ("savings_goals", "current_amount", False),
        ("cards", "spending_limit", True),
    ):
        op.alter_column(
            table,
            column,
            existing_type=sa.Float(),
            type_=sa.Numeric(18, 2),
            existing_nullable=nullable,
        )


def downgrade():
    raise RuntimeError(
        "Production repair is intentionally irreversible; "
        "restore from a verified database backup instead."
    )
