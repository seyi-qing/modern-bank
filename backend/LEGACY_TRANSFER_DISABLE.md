# Legacy transfer endpoint

After deploying Banking Core v2.1, do not expose the old `POST /api/v1/banking/transfer` implementation. It mutates balances directly and predates the ledger/idempotency layer.

The frontend should call `POST /api/v1/banking/v2/transfer`. During integration, replace the old transfer route with HTTP 410 or remove it after clients have migrated.
