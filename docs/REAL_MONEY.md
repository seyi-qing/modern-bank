# Real money path

This prototype uses **Stripe test mode** patterns (PaymentIntents, webhooks).

Live funds require:

1. Bank charter, MTL licenses, or BaaS sponsorship
2. Live processor approval + underwriting
3. BSA/AML program, KYC, monitoring
4. Proper ledger, reconciliation, chargeback handling
5. Secrets vault, PCI scope reduction, audits

Keep `ENABLE_LIVE_PAYMENTS=false` until legal clearance.
This is not a substitute for licensing or a compliance program.
