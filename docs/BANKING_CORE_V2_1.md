# ModernBank Banking Core v2.1

## What changed

1. **Double-entry ledger** — every completed internal transfer creates one journal with exactly one debit and one credit for the same amount/currency.
2. **Atomic transfer** — account locks, transaction creation, journal posting, balance-cache updates, and notifications are committed as one database transaction.
3. **Idempotency** — client provides a unique key (JSON body and/or `Idempotency-Key` header). Repeating the same request returns the original transaction. Reusing a key with different parameters returns `409`.
4. **Reconciliation** — admin compares cached account balance against ledger-derived balance.
5. **Admin transaction operations** — flagged transfers can be approved (posts ledger) or rejected (never moves money). Actions are audit-logged.

## Endpoints

- `POST /api/v1/banking/v2/transfer`
- `GET /api/v1/banking/v2/transactions/{transaction_id}`
- `POST /api/v1/admin/core/transactions/{transaction_id}/review`
- `GET /api/v1/admin/core/reconciliation`
- `GET /api/v1/admin/core/reconciliation/{account_id}`

## Apply order

1. Copy models/services/routers/migrations from this release.
2. Register ledger models in Alembic env and include routers in `main.py`.
3. `alembic upgrade head` on a **staging/copy** database.
4. `python -m scripts.create_opening_balances` (from backend).
5. Admin reconciliation must return `ok: true` before enabling transfers.
6. Point clients at `/banking/v2/transfer`; disable legacy `/banking/transfer`.

## Safety rules

- Never update `Account.balance` from an admin UI.
- Never mark a transfer COMPLETED without a balanced journal.
- Never accept a transfer without an idempotency key.
- Never use floating-point for money — use `NUMERIC(18,2)` / `Decimal`.
- Do not auto-seed demo data on production startup.
