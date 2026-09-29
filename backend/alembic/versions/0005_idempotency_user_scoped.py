"""Scope transaction idempotency keys per user (dev chain after 0004).

Replaces a global unique index on idempotency_key with
UNIQUE (user_id, idempotency_key) so different users may reuse the same client key.
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_idempotency_user_scoped"
down_revision = "0004_ledger_system_accounts"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Drop known global unique indexes/constraints if present
        op.execute(
            sa.text(
                "DROP INDEX IF EXISTS ix_transactions_idempotency_key"
            )
        )
        op.execute(
            sa.text(
                "ALTER TABLE transactions DROP CONSTRAINT IF EXISTS "
                "transactions_idempotency_key_key"
            )
        )
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_transactions_user_idempotency "
                "ON transactions (user_id, idempotency_key) "
                "WHERE idempotency_key IS NOT NULL"
            )
        )
    else:
        # SQLite / batch: best-effort
        with op.batch_alter_table("transactions") as batch:
            try:
                batch.create_unique_constraint(
                    "uq_transactions_user_idempotency",
                    ["user_id", "idempotency_key"],
                )
            except Exception:
                pass


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text("DROP INDEX IF EXISTS uq_transactions_user_idempotency"))
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_transactions_idempotency_key "
                "ON transactions (idempotency_key)"
            )
        )
