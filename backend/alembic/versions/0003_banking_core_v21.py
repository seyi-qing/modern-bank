"""Banking Core v2.1 ledger and idempotency migration.

Back up the database first. Review SQL before applying to any shared environment.
On current main (no prior foundation revisions), this is the first ledger revision.
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_banking_core_v21"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "transactions" not in tables or "accounts" not in tables:
        raise RuntimeError("Run the existing ModernBank base schema before Banking Core v2.1 migration")

    cols = {c["name"] for c in inspector.get_columns("transactions")}
    if "idempotency_key" not in cols:
        op.add_column("transactions", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
        op.create_index("ix_transactions_idempotency_key", "transactions", ["idempotency_key"], unique=True)

    with op.batch_alter_table("accounts") as batch:
        batch.alter_column("balance", existing_type=sa.Float(), type_=sa.Numeric(18, 2), existing_nullable=False)
    with op.batch_alter_table("transactions") as batch:
        batch.alter_column("amount", existing_type=sa.Float(), type_=sa.Numeric(18, 2), existing_nullable=False)
    if "savings_goals" in tables:
        with op.batch_alter_table("savings_goals") as batch:
            batch.alter_column("target_amount", existing_type=sa.Float(), type_=sa.Numeric(18, 2), existing_nullable=False)
            batch.alter_column("current_amount", existing_type=sa.Float(), type_=sa.Numeric(18, 2), existing_nullable=False)
    if "cards" in tables:
        with op.batch_alter_table("cards") as batch:
            batch.alter_column("spending_limit", existing_type=sa.Float(), type_=sa.Numeric(18, 2), existing_nullable=True)

    if "ledger_accounts" not in tables:
        op.create_table(
            "ledger_accounts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False, unique=True),
            sa.Column("currency", sa.String(length=3), nullable=False),
        )
        op.create_index("ix_ledger_accounts_account_id", "ledger_accounts", ["account_id"], unique=True)

    direction = sa.Enum("debit", "credit", name="ledgerentrydirection")
    if bind.dialect.name == "postgresql":
        direction.create(bind, checkfirst=True)

    if "ledger_journals" not in tables:
        op.create_table(
            "ledger_journals",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transactions.id"), nullable=True, unique=True),
            sa.Column("reference", sa.String(length=100), nullable=False, unique=True),
            sa.Column("currency", sa.String(length=3), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_ledger_journals_transaction_id", "ledger_journals", ["transaction_id"], unique=True)
        op.create_index("ix_ledger_journals_reference", "ledger_journals", ["reference"], unique=True)

    if "ledger_entries" not in tables:
        op.create_table(
            "ledger_entries",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("journal_id", sa.Integer(), sa.ForeignKey("ledger_journals.id"), nullable=False),
            sa.Column("ledger_account_id", sa.Integer(), sa.ForeignKey("ledger_accounts.id"), nullable=False),
            sa.Column("direction", direction, nullable=False),
            sa.Column("amount", sa.Numeric(18, 2), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_ledger_entries_journal_id", "ledger_entries", ["journal_id"])
        op.create_index("ix_ledger_entries_ledger_account_id", "ledger_entries", ["ledger_account_id"])
        op.create_index("ix_ledger_entries_journal_direction", "ledger_entries", ["journal_id", "direction"])

    if "audit_logs" not in tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("action", sa.String(length=80), nullable=False),
            sa.Column("resource_type", sa.String(length=80), nullable=False),
            sa.Column("resource_id", sa.String(length=120), nullable=True),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("before_data", sa.JSON(), nullable=True),
            sa.Column("after_data", sa.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(length=64), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
        op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])


def downgrade():
    op.drop_table("audit_logs")
    op.drop_index("ix_ledger_entries_journal_direction", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_ledger_account_id", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_journal_id", table_name="ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_index("ix_ledger_journals_reference", table_name="ledger_journals")
    op.drop_index("ix_ledger_journals_transaction_id", table_name="ledger_journals")
    op.drop_table("ledger_journals")
    op.drop_index("ix_ledger_accounts_account_id", table_name="ledger_accounts")
    op.drop_table("ledger_accounts")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="ledgerentrydirection").drop(bind, checkfirst=True)
    op.drop_index("ix_transactions_idempotency_key", table_name="transactions")
    op.drop_column("transactions", "idempotency_key")
