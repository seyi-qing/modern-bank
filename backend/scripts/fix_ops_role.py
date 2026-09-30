"""Inspect ops user role and force a known-good label if needed.

Does not touch balances. Safe to run anytime.

  python -m scripts.fix_ops_role
"""
from sqlalchemy import text
from app.core.database import SessionLocal

EMAIL = "ops@modernbank.dev"


def main():
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT id, email, role::text, is_active FROM users WHERE email = :e"),
            {"e": EMAIL},
        ).first()
        if not row:
            print(f"No user {EMAIL}")
            return
        print(f"Found id={row[0]} email={row[1]} role={row[2]!r} active={row[3]}")

        labels = [
            r[0]
            for r in db.execute(
                text(
                    """
                    SELECT e.enumlabel FROM pg_enum e
                    JOIN pg_type t ON t.oid = e.enumtypid
                    JOIN pg_attribute a ON a.atttypid = t.oid
                    JOIN pg_class c ON c.oid = a.attrelid
                    WHERE c.relname = 'users' AND a.attname = 'role' AND NOT a.attisdropped
                    """
                )
            ).fetchall()
        ]
        print(f"Enum labels: {labels}")

        typ = db.execute(
            text(
                """
                SELECT t.typname FROM pg_attribute a
                JOIN pg_class c ON c.oid = a.attrelid
                JOIN pg_type t ON t.oid = a.atttypid
                WHERE c.relname = 'users' AND a.attname = 'role' AND NOT a.attisdropped
                """
            )
        ).scalar()

        # Prefer operations if present, else customer (always safe)
        target = None
        for cand in ("operations", "OPERATIONS", "customer", "CUSTOMER"):
            if cand in labels:
                target = cand
                if cand.lower() == "operations":
                    break
        if not target:
            target = "customer" if "customer" in [x.lower() for x in labels] else labels[0]

        # normalize: pick exact label matching lower
        for lab in labels:
            if lab.lower() == target.lower():
                target = lab
                break

        db.execute(
            text(f"UPDATE users SET role = CAST(:r AS {typ}) WHERE id = :id"),
            {"r": target, "id": row[0]},
        )
        db.commit()
        print(f"Set role to {target!r}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
