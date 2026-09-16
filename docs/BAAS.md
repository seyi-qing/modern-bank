# BaaS layer (Unit-inspired simulation)

Hold / Move / Spend / Lend under `/api/v1/baas/*`.

**Simulation only** — not connected to Unit, FedACH, or card networks.

| Pillar | Endpoints |
|--------|-----------|
| Hold | POST/GET `/baas/accounts` |
| Move | POST/GET `/baas/payments` |
| Spend | POST/GET `/baas/cards`, freeze |
| Lend | POST/GET `/baas/credit-accounts` |

UI: Dashboard → BaaS Hub.

To go live: partner with a BaaS provider + bank; replace this sim with their API and webhooks.
