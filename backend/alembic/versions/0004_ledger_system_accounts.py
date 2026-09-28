"""Add system/control ledger accounts for controlled opening balances."""
from alembic import op
import sqlalchemy as sa

revision = "0004_ledger_system_accounts"
down_revision = "0003_banking_core_v21"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    with op.batch_alter_table("ledger_accounts") as batch:
        batch.alter_column("account_id", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column("code", sa.String(length=100), nullable=True))
        batch.add_column(sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()))
    bind.execute(sa.text(
        "UPDATE ledger_accounts SET code = 'ACCOUNT:' || CAST(account_id AS VARCHAR(50)) WHERE code IS NULL"
    ))
    with op.batch_alter_table("ledger_accounts") as batch:
        batch.alter_column("code", existing_type=sa.String(length=100), nullable=False)
        batch.create_unique_constraint("uq_ledger_accounts_code", ["code"])


def downgrade():
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM ledger_accounts WHERE is_system = true"))
    with op.batch_alter_table("ledger_accounts") as batch:
        batch.drop_constraint("uq_ledger_accounts_code", type_="unique")
        batch.drop_column("is_system")
        batch.drop_column("code")
        batch.alter_column("account_id", existing_type=sa.Integer(), nullable=False)
