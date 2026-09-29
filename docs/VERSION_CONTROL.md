# ModernBank Version Control Policy

## Stable baseline

- `main` is the protected, deployable branch.
- Production releases are identified by immutable semantic-version tags such as `v2.1.0`.
- Never force-push to `main`.
- Never move an existing release tag to a different commit.

## Branches

Use short-lived branches:

- `feat/*` — new functionality
- `fix/*` — bug fixes
- `chore/*` — maintenance, tooling, documentation
- `hotfix/*` — urgent production fixes

Create every new branch from the current `main` unless the work explicitly depends on another branch.

## Pull requests

All changes to `main` must go through a pull request.

Before merge:

1. Review the changed files and database/migration impact.
2. Run the relevant test suite and CI checks.
3. Confirm no secrets or production credentials are committed.
4. Confirm migrations are safe and ordered.
5. Confirm the change does not bypass double-entry ledger controls, idempotency, authorization, audit, or reconciliation safeguards.

## Releases

- Use semantic versioning: `MAJOR.MINOR.PATCH`.
- Release only from `main`.
- Tag the exact release commit.
- Keep release notes describing the material changes and verification status.

## Banking safety rule

Changes affecting balances, ledger entries, transfers, idempotency, reconciliation, migrations, authorization, or audit trails require explicit review of both application behavior and database impact before release.
