"""Create card_requests table (production chain after 0009).

Reuses existing PostgreSQL enum `cardtype` (from cards table).
Does not CREATE TYPE cardtype.
"""
from alembic import op

revision = "0010_card_requests"
down_revision = "0009_staff_roles"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # SQLite / other: simple table without PG enums
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS card_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                card_type VARCHAR(20) NOT NULL,
                label VARCHAR(50),
                spending_limit NUMERIC(18, 2),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                review_reason TEXT,
                reviewed_by_user_id INTEGER,
                issued_card_id INTEGER,
                created_at TIMESTAMP,
                reviewed_at TIMESTAMP
            )
            """
        )
        return

    exists = bind.exec_driver_sql(
        "SELECT to_regclass('public.card_requests') IS NOT NULL"
    ).scalar()
    if exists:
        return

    # New enum only — never recreate cardtype
    bind.exec_driver_sql(
        """
        DO $$ BEGIN
            CREATE TYPE cardrequeststatus AS ENUM ('pending', 'approved', 'rejected');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    bind.exec_driver_sql(
        """
        CREATE TABLE card_requests (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            card_type cardtype NOT NULL,
            label VARCHAR(50),
            spending_limit NUMERIC(18, 2),
            status cardrequeststatus NOT NULL DEFAULT 'pending',
            review_reason TEXT,
            reviewed_by_user_id INTEGER REFERENCES users(id),
            issued_card_id INTEGER REFERENCES cards(id),
            created_at TIMESTAMPTZ,
            reviewed_at TIMESTAMPTZ
        )
        """
    )
    bind.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_card_requests_user_id ON card_requests (user_id)"
    )
    bind.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_card_requests_status ON card_requests (status)"
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS card_requests")
    op.execute("DROP TYPE IF EXISTS cardrequeststatus")
