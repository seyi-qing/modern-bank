"""Reconcile the legacy production schema with Banking Core v2.1.

This revision repairs a legacy create_all schema that already contains the
v2.1 ledger tables but lacks Alembic tracking and transfer idempotency.

It does not create/drop business tables or fabricate historical journals.
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
            "Production schema repair requires existing Banking Core tables; "
            f"missing: {', '.join(sorted(missing))}"
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

    op.alter_column("accounts", "balance",
        existing_type=sa.Float(), type_=sa.Numeric(18, 2), existing_nullable=False)
    op.alter_column("transactions", "amount",
        existing_type=sa.Float(), type_=sa.Numeric(18, 2), existing_nullable=False)
    op.alter_column("savings_goals", "target_amount",
        existing_type=sa.Float(), type_=sa.Numeric(18, 2), existing_nullable=False)
    op.alter_column("savings_goals", "current_amount",
        existing_type=sa.Float(), type_=sa.Numeric(18, 2), existing_nullable=False)
    op.alter_column("cards", "spending_limit",
        existing_type=sa.Float(), type_=sa.Numeric(18, 2), existing_nullable=True)


def downgrade():
    raise RuntimeError(
        "Production schema repair is intentionally irreversible; "
        "restore from a verified database backup instead."
    )
