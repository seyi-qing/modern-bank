# Migration Safety and Database State

## Purpose

ModernBank has two historical schema paths that must not be confused:

1. **Existing/legacy databases** were originally created by SQLAlchemy `Base.metadata.create_all()` during application startup.
2. **Banking Core v2.1** was introduced later through Alembic migrations `0003` and `0004`.

There are currently no `0001` or `0002` Alembic revisions in this repository. Therefore `0003_banking_core_v21` is **not** a clean-from-zero baseline migration.

## Known upgrade chain

For an existing ModernBank database, the intended historical sequence is:

```text
legacy SQLAlchemy create_all schema
        |
        v
0003_banking_core_v21
        |
        v
0004_ledger_system_accounts
```

### 0003 — Banking Core v2.1

`0003_banking_core_v21` assumes the legacy `accounts` and `transactions` tables already exist.

It adds the Banking Core v2.1 ledger tables and upgrades selected monetary/idempotency fields.

It must **not** be treated as an initial schema for an empty database.

### 0004 — Ledger system accounts

`0004_ledger_system_accounts` depends on `0003`.

It makes ledger-account system/control-account support explicit through:

- nullable customer `account_id`
- unique `code`
- `is_system`

## Safe operating rules

Before touching an existing database:

1. Run the read-only diagnostic:
   ```bash
   python backend/scripts/check_migration_state.py
   ```
2. Record the reported state and Alembic revision.
3. Verify the actual database before choosing an Alembic command.
4. Back up production data before any write migration.
5. Apply migrations only after the database state is positively identified.

### The diagnostic does not mutate the database

`check_migration_state.py`:

- does not call `alembic upgrade`
- does not call `alembic stamp`
- does not call `create_all()`
- does not create or drop tables
- does not alter rows
- does not commit changes

## Do not do these yet

Until the real database state has been inspected:

- **Do not** create a replacement `0001_initial.py`.
- **Do not** rewrite `0003_banking_core_v21`.
- **Do not** rewrite `0004_ledger_system_accounts`.
- **Do not** change their `down_revision` values.
- **Do not** run `alembic stamp`.
- **Do not** run `alembic upgrade`.
- **Do not** drop/recreate tables.
- **Do not** perform a global Float-to-Decimal migration.

## Fresh-install strategy

A clean baseline migration may be added later for new installations, but it should be introduced as a deliberate new release strategy.

It must not be created by pretending that `0003` is the original schema, because existing databases may already contain data created outside Alembic.

The eventual clean-install strategy should be validated against:

- all SQLAlchemy models
- all foreign keys and indexes
- enum definitions
- audit/BaaS/ledger tables
- application startup
- Alembic upgrade/downgrade behavior

## Existing-production strategy

For an existing database, the next step is **inspection, not migration**.

The production database should be classified as one of:

- `EMPTY_OR_FRESH`
- `LEGACY_CREATE_ALL_BASELINE`
- `BANKING_CORE_V21_0003`
- `BANKING_CORE_V21_PLUS_0004`
- `BANKING_CORE_V21_UNSTAMPED_OR_UNKNOWN_REVISION`
- `UNKNOWN_OR_PARTIAL_SCHEMA`

An unknown or partial state requires manual review. The application must not guess and automatically repair it.

## Why this exists

Banking migrations are different from ordinary application schema changes. A wrong migration baseline can:

- mark an existing database as migrated when it is not
- attempt to recreate existing tables
- destroy or reinterpret financial data
- make reconciliation unreliable
- leave Alembic history inconsistent with the actual schema

The safest rule for ModernBank is:

> **Inspect first. Identify the baseline. Back up. Then migrate deliberately.**

This document is a safety boundary for the Banking Core v2.1 work.
