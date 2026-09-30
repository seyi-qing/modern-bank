# Control plane RBAC (feat/control-plane-rbac)

## Roles

| Role | Purpose |
|------|---------|
| `admin` | Full control plane (existing super-admin) |
| `operations` | Customers, activity, freeze accounts, view flagged |
| `risk_analyst` | Flagged review (approve/reject), activity |
| `finance` | Stats, activity, reconciliation |
| `card_operations` | Card ops (product workflow next) |
| `compliance` | Users / KYC status |
| `auditor` | Read-only: users, activity, recon |
| `customer` | Retail banking only |

## Permissions

Defined in `backend/app/core/permissions.py`.

Examples:
- `transactions:review` → risk_analyst, admin
- `reconciliation:read` → finance, auditor, admin
- `accounts:freeze` → operations, admin
- Role changes → **admin only**

## Endpoints

- `GET /admin/me/permissions` — current staff grants
- `POST /admin/accounts/{id}/freeze` / `unfreeze` — no balance mutation
- Existing admin routes now call `require_perm(...)`

## Migration (Neon main)

```bash
alembic upgrade 0009_staff_roles
```

Or Neon SQL:

```sql
-- replace userrole with actual typname if different
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'operations';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'risk_analyst';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'finance';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'card_operations';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'compliance';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'auditor';
```

## Assign a staff role

Only as `admin`:

```http
PATCH /api/v1/admin/users/{id}
{ "role": "risk_analyst" }
```
