"""Scope transaction idempotency keys per user (production baseline chain).

After 0007_production_schema_repair. Same semantics as 0005 on the other branch.
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_idempotency_user_scoped"
down_revision = "0007_production_schema_repair"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(sa.text("DROP INDEX IF EXISTS ix_transactions_idempotency_key"))
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


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(sa.text("DROP INDEX IF EXISTS uq_transactions_user_idempotency"))
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_transactions_idempotency_key "
            "ON transactions (idempotency_key)"
        )
    )
