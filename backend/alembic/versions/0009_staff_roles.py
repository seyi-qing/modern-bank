"""Add staff RBAC roles to userrole enum (production chain).

PostgreSQL: ALTER TYPE ... ADD VALUE (cannot run inside a transaction block
on older PG — Neon supports ADD VALUE IF NOT EXISTS on modern versions).
"""
from alembic import op

revision = "0009_staff_roles"
down_revision = "0008_idempotency_user_scoped"
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

    # Detect actual enum type name for users.role
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
    # Removing enum values is not safe; leave roles in place.
    pass
