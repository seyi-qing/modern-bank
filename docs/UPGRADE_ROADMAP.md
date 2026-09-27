# ModernBank — Production upgrade roadmap

> Honest scope: this is an **educational banking prototype**, not a licensed bank.
> "Production-ready" here means: solid demo product, clean architecture, shippable UI,
> and a clear path if you later partner with a BaaS (Unit, Treasury Prime, Synapse alternatives).

## Current state (as of this commit)

### Backend — strong foundation
| Module | Status |
|--------|--------|
| JWT auth + roles (customer/admin) | Done |
| Accounts, internal transfers | Done |
| Fraud scoring (heuristic) | Done |
| Cards (issue / freeze) | Done |
| Notifications + WebSocket manager | Done |
| BaaS models (deposit, wallet, credit) | Done |
| Stripe deposit-intent skeleton | Partial |
| Alembic / Docker | Present |

### Frontend — was a shell; core pages added
| Route | Status |
|-------|--------|
| `/` landing | Exists (sparse) |
| `/login` | Exists |
| `/register` | **Added** |
| `/dashboard` overview | **Added** |
| `/dashboard/transfer` | **Added** |
| `/dashboard/transactions` | **Added** |
| `/dashboard/cards` | **Added** |
| `/dashboard/baas` | **Added** (read path) |
| `/dashboard/goals` · insights · notifications | **Added** |
| `/dashboard/deposit` | Stub (Stripe next) |
| `/admin/*` pages | Layout only — still needed |

## Critical gaps before calling it "stunning / production demo"

1. **Admin UI pages** (`/admin`, users, flagged) — API exists, UI missing.
2. **Landing redesign** — current hero is empty navy void; needs product story + trust bar + feature grid.
3. **Money path polish** — confirm transfer to self-owned second account in seed; document account numbers on dashboard for demos.
4. **Atomic transfers** — backend should use DB transactions / `SELECT FOR UPDATE` on balances (race conditions).
5. **No random in fraud score in prod demos** — remove `random.uniform` in `fraud_engine.py` for determinism.
6. **Refresh tokens** — stored client-side but rotation/revoke not fully wired.
7. **Tests** — zero automated tests in repo; add API smoke + transfer integrity tests.
8. **Observability** — structured logs, request IDs, basic metrics.

## Design system direction (graphics)

Keep dark fintech, but tighten:
- **Type**: Inter is fine; add a mono for account numbers (IBM Plex Mono).
- **Color**: brand blue is generic SaaS — consider deeper ink + one electric accent (or your portfolio teal for brand continuity).
- **Cards**: physical metaphor (already started on dashboard) — emboss, chip mark, subtle noise.
- **Motion**: 150–200ms ease on balance updates; avoid flashy gradients everywhere.
- **Density**: banking UIs win on scanability — tables, clear debit/credit color, status chips.

## Suggested next 7-day plan

| Day | Ship |
|-----|------|
| 1 | Admin pages + flagged queue actions |
| 2 | Landing redesign + meta/OG |
| 3 | Transfer integrity (DB locks) + remove fraud randomness |
| 4 | Stripe test deposit end-to-end |
| 5 | Seed richer demo activity + show account numbers in UI |
| 6 | Playwright smoke: login → transfer → activity |
| 7 | README + architecture diagram refresh |

## Legal / compliance (do not skip)

- Keep **"Educational demo — not a real bank"** on every public surface.
- Never imply FDIC, real routing, or licensed money transmission.
- Real money requires licensed partner + KYC/AML program — see `docs/REAL_MONEY.md`.

## File map (frontend after this upgrade)

```
frontend/
  app/
    page.tsx                 # marketing landing
    (auth)/login|register/   # auth
    dashboard/
      layout.tsx             # auth gate + sidebar shell
      page.tsx               # overview
      transfer|transactions|cards|baas|goals|insights|notifications|deposit/
    admin/layout.tsx         # admin shell (pages TBD)
  components/layout/Sidebar.tsx
  components/ui/Card.tsx
  lib/api.ts | store.ts | format.ts
```
