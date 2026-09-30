"""Add staff RBAC roles (dev chain after 0005)."""
from alembic import op

revision = "0005b_staff_roles_dev"
down_revision = "0005_idempotency_user_scoped"
branch_labels = None
depends_on = None

_NEW_ROLES = (
    "operations",
    "risk_analyst",
    "finance",
    "card_operations",
    "compliance",
    "auditor",
)


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    row = bind.exec_driver_sql(
        """
        SELECT t.typname
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_type t ON t.oid = a.atttypid
        WHERE c.relname = 'users' AND a.attname = 'role' AND NOT a.attisdropped
        """
    ).first()
    if not row:
        return
    typname = row[0]
    for value in _NEW_ROLES:
        bind.exec_driver_sql(
            f"ALTER TYPE {typname} ADD VALUE IF NOT EXISTS '{value}'"
        )


def downgrade():
    pass
