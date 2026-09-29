"""Record the verified legacy production schema as an Alembic baseline.

This revision is intentionally a no-op. It exists because the original
production database was created by SQLAlchemy create_all() before Alembic
history was introduced. The database already contains the structures covered
by 0003/0004 plus the production repair changes.

Do not use this revision to create or modify business tables.
"""
from alembic import op

revision = "0006_production_baseline"
down_revision = "0005_production_schema_repair"
branch_labels = None
depends_on = None


def upgrade():
    # Baseline marker only; verified production schema already exists.
    pass


def downgrade():
    raise RuntimeError(
        "Production baseline is intentionally irreversible; "
        "restore from a verified database backup instead."
    )
