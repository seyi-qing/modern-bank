# Banking Core v2.1.1 — Hardening (feat/core-hardening)

## Goals

Close known correctness gaps before expanding the control plane.

| Item | Change |
|------|--------|
| Legacy transfer | `POST /banking/transfer` → **HTTP 410** |
| Money ORM | `Numeric(18,2)` / `Decimal` on balances, amounts, goals, limits |
| Idempotency | Unique per `(user_id, idempotency_key)` (partial index where key not null) |
| Admin review + audit | Already committed together in `admin_core_v21.review` |
| Bootstrap | `python -m scripts.create_admin` (env-based, not startup) |
| Tests | Idempotency, cross-user key reuse, flag→approve→recon |

## Migrations

- Dev / 0003-chain: `0005_idempotency_user_scoped`
- Production / 0006-chain: `0008_idempotency_user_scoped`

On Neon main (production baseline):

```bash
cd backend
source .venv/bin/activate
export DATABASE_URL="postgresql://…main…?sslmode=require"
alembic upgrade 0008_idempotency_user_scoped
# or: alembic upgrade head   # if this branch is current head on that lineage
```

If `alembic_version` is on `0007_production_schema_repair`, upgrade to `0008`.

## Bootstrap admin (fresh DB only)

```bash
export BOOTSTRAP_ADMIN_EMAIL="ops@example.com"
export BOOTSTRAP_ADMIN_PASSWORD="StrongPass123!"
python -m scripts.create_admin
```

Does not delete or alter existing `admin@modernbank.dev` rows.

## Merge path

1. CI green on `feat/core-hardening`
2. PR → `main`
3. Tag `v2.1.1` after deploy + recon still `ok: true`
4. Next branch: `feat/control-plane-rbac`
