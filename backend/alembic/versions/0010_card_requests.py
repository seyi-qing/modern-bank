"""Create card_requests table (production chain after 0009)."""
from alembic import op
import sqlalchemy as sa

revision = "0010_card_requests"
down_revision = "0009_staff_roles"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "card_requests" in inspector.get_table_names():
        return

    cardtype = sa.Enum("virtual", "physical", name="cardtype", create_type=False)
    reqstatus = sa.Enum("pending", "approved", "rejected", name="cardrequeststatus", create_type=True)

    op.create_table(
        "card_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("card_type", cardtype, nullable=False),
        sa.Column("label", sa.String(50), nullable=True),
        sa.Column("spending_limit", sa.Numeric(18, 2), nullable=True),
        sa.Column("status", reqstatus, nullable=False, server_default="pending"),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("issued_card_id", sa.Integer(), sa.ForeignKey("cards.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_card_requests_user_id", "card_requests", ["user_id"])
    op.create_index("ix_card_requests_status", "card_requests", ["status"])


def downgrade():
    op.drop_table("card_requests")
    op.execute("DROP TYPE IF EXISTS cardrequeststatus")
