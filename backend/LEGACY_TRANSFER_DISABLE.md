# Legacy transfer endpoint — DISABLED (v2.1.1)

`POST /api/v1/banking/transfer` returns **HTTP 410 Gone**.

It previously mutated balances without the double-entry ledger or idempotency.

## Correct path

```http
POST /api/v1/banking/v2/transfer
Authorization: Bearer <access_token>
Idempotency-Key: <client-generated-uuid>
Content-Type: application/json

{
  "from_account_id": 2,
  "to_account_number": "…",
  "amount": "25.00",
  "currency": "USD",
  "description": "optional",
  "idempotency_key": "same-as-header"
}
```

Frontend `lib/api.ts` already calls `/banking/v2/transfer`.

Do not re-enable the legacy route without a full ledger migration path.
