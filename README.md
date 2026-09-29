# ModernBank — Banking Core v2.1

Production-oriented digital banking application built with **Next.js** and **FastAPI**.

> **Important:** ModernBank is software infrastructure, not a bank or deposit-taking institution. Operating live customer funds requires the appropriate licensing, regulated banking/BaaS arrangements, compliance controls, and production infrastructure.

## Current baseline

The current stable engineering baseline is **v2.1.0**.

The v2.1 release focuses on banking-core correctness and operational safety, including:

- double-entry ledger controls
- atomic transfers
- transfer idempotency
- Decimal-safe monetary calculations
- reconciliation and flagged-transaction workflows
- administrative transaction review and audit handling
- migration-state diagnostics and guarded schema repair
- isolated staging application verification
- backend CI coverage
- removal of startup demo-data seeding
- migration and upgrade-chain safety documentation

See the immutable **v2.1.0** release for the exact release commit and verification record.

## Repository workflow

- `main` is the protected, deployable branch.
- Releases use immutable semantic-version tags such as `v2.1.0`.
- New work uses short-lived branches:
  - `feat/*` — new functionality
  - `fix/*` — bug fixes
  - `chore/*` — maintenance, tooling, documentation
  - `hotfix/*` — urgent production fixes
- Changes reach `main` through pull requests and CI.
- Existing release tags must never be moved to another commit.
- Never force-push to `main`.

See [docs/VERSION_CONTROL.md](docs/VERSION_CONTROL.md) for the full policy.

## Backend

The backend is a FastAPI application under `backend/`.

### Local development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API documentation is available at `http://localhost:8000/docs` when running locally.

### Tests

The repository's GitHub Actions workflow runs the backend unit tests and the staging application tests. Pull requests targeting `main` are validated by CI, and pushes to `main` also run the backend workflow.

Run the core suite locally with:

```bash
cd backend
python -m unittest tests.test_banking_core_v21 tests.test_migration_state -v
```

The staging application test requires a configured staging database and should only be run against the designated staging environment.

## Frontend

The frontend is under `frontend/`.

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` to the URL of the deployed API when configuring a deployed frontend.

## Production safety

Do not commit secrets, production database credentials, or customer data.

Changes affecting balances, ledger entries, transfers, idempotency, reconciliation, migrations, authorization, or audit trails require explicit review of application behavior and database impact before release.

## License

MIT — see the repository license file.
