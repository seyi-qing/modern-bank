"""
One-shot bootstrap for a staff admin user.

Does NOT run at application startup. Existing Neon users are left alone.

Usage:
  export DATABASE_URL="postgresql://…"
  export BOOTSTRAP_ADMIN_EMAIL="ops@example.com"
  export BOOTSTRAP_ADMIN_PASSWORD="StrongPass123!"
  export BOOTSTRAP_ADMIN_NAME="Ops Admin"   # optional
  python -m scripts.create_admin

Idempotent: if email already exists, prints status and exits 0 without changing password.
"""
from __future__ import annotations

import os
import sys

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.services.audit import write_audit


def main() -> int:
    email = (os.environ.get("BOOTSTRAP_ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD") or ""
    name = (os.environ.get("BOOTSTRAP_ADMIN_NAME") or "System Administrator").strip()

    if not email or "@" not in email:
        print("BOOTSTRAP_ADMIN_EMAIL is required", file=sys.stderr)
        return 2
    if len(password) < 8:
        print("BOOTSTRAP_ADMIN_PASSWORD must be at least 8 characters", file=sys.stderr)
        return 2

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(
                f"User already exists id={existing.id} email={existing.email} "
                f"role={existing.role.value} — no password change."
            )
            return 0

        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=name,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            kyc_status="verified",
        )
        db.add(user)
        db.flush()
        write_audit(
            db,
            actor=user,
            action="BOOTSTRAP_ADMIN",
            resource_type="user",
            resource_id=user.id,
            reason="Explicit one-shot create_admin bootstrap",
            before=None,
            after={"email": email, "role": "admin"},
            request=None,
        )
        db.commit()
        print(f"Created admin user id={user.id} email={user.email}")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Bootstrap failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
