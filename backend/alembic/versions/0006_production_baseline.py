"""Production baseline marker for the verified legacy ModernBank schema.

This is a separate Alembic root because the original production database was
created by SQLAlchemy create_all() and never executed revisions 0003/0004.

Production rollout procedure:
1. Take/verify a database backup.
2. Run the separately reviewed production repair migration.
3. Verify schema, balances, ledger integrity, and row counts.
4. Stamp this revision only after those checks pass.

This marker performs no schema changes.
"""
revision = "0006_production_baseline"
down_revision = None
branch_labels = ("production_baseline",)
depends_on = None

from alembic import op


def upgrade():
    pass


def downgrade():
    raise RuntimeError(
        "Production baseline is intentionally irreversible; "
        "restore from a verified database backup instead."
    )
