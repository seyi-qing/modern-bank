# Apply Banking Core v2.1 (practical steps)

## 1. Code already on GitHub

These paths were added on `main`:

- `backend/app/models/ledger.py`
- `backend/app/models/audit.py`
- `backend/app/models/schemas_banking_core_v21.py`
- `backend/app/services/ledger_service.py`
- `backend/app/services/banking_core_v21.py`
- `backend/app/services/fraud_engine_v21.py`
- `backend/app/services/audit.py`
- `backend/app/routers/banking_core_v21.py`
- `backend/app/routers/admin_core_v21.py`
- `backend/alembic/versions/0003_banking_core_v21.py`
- `backend/alembic/versions/0004_ledger_system_accounts.py`
- `backend/scripts/create_opening_balances.py`
- `backend/tests/test_banking_core_v21.py`

## 2. Wire routers (if not already)

In `backend/app/main.py`:

```python
from app.routers import banking_core_v21, admin_core_v21
from app.models import ledger as ledger_models  # noqa: F401
from app.models import audit as audit_models  # noqa: F401

app.include_router(banking_core_v21.router, prefix=settings.API_PREFIX)
app.include_router(admin_core_v21.router, prefix=settings.API_PREFIX)
```

In `backend/alembic/env.py`, import ledger + audit models so metadata includes them.

Ensure `Transaction` has `idempotency_key` column (migration 0003 adds it if missing).

## 3. Staging database only

```bash
cd backend
# backup first
alembic upgrade head
python -m scripts.create_opening_balances
pytest tests/test_banking_core_v21.py -q
```

## 4. Admin check

```bash
# as admin JWT
GET /api/v1/admin/core/reconciliation
# require: "ok": true
```

## 5. Cut over transfers

- Frontend: `POST /api/v1/banking/v2/transfer` + `Idempotency-Key` header
- Disable legacy `POST /api/v1/banking/transfer` (see `backend/LEGACY_TRANSFER_DISABLE.md`)

## 6. Admin UI next

- Flagged queue → Approve/Reject with reason → `POST /admin/core/transactions/{id}/review`
- Reconciliation page → `GET /admin/core/reconciliation`
- Never add edit-balance controls
