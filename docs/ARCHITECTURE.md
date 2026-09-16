# ModernBank Architecture

## Stack

- Frontend: Next.js 14 (App Router), TypeScript, Tailwind, Zustand
- Backend: FastAPI, SQLAlchemy 2, Alembic, JWT auth
- DB: SQLite (local) / PostgreSQL (Docker)
- Payments: Stripe test-mode PaymentIntents + webhooks
- Realtime: WebSocket notifications

## Layout

```
Browser (Next.js)
  → JWT + HTTPS
FastAPI
  → Auth / Banking / Admin / Cards / Payments / BaaS / Notifications
SQLAlchemy → SQLite or Postgres
```

## Design notes

1. API-first under `/api/v1`
2. Role-based JWT (`customer` | `admin`)
3. Fraud heuristics on transfers (explainable score)
4. Ledger updates in the same DB transaction as the transfer
5. BaaS layer simulates Unit-style Hold/Move/Spend/Lend
