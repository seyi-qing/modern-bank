import unittest

from scripts.check_migration_state import (
    LEDGER_TABLES,
    classify,
)


class MigrationStateClassificationTests(unittest.TestCase):
    def test_empty_or_fresh(self):
        self.assertEqual(
            classify(set(), set(), set(), None),
            "EMPTY_OR_FRESH",
        )

    def test_legacy_create_all_baseline(self):
        tables = {"users", "accounts", "transactions"}
        self.assertEqual(
            classify(tables, {"id", "amount"}, set(), None),
            "LEGACY_CREATE_ALL_BASELINE",
        )

    def test_banking_core_0003(self):
        tables = {"users", "accounts", "transactions", *LEDGER_TABLES}
        self.assertEqual(
            classify(
                tables,
                {"id", "amount", "idempotency_key"},
                {"account_id"},
                "0003_banking_core_v21",
            ),
            "BANKING_CORE_V21_0003",
        )

    def test_banking_core_0004(self):
        tables = {"users", "accounts", "transactions", *LEDGER_TABLES}
        self.assertEqual(
            classify(
                tables,
                {"id", "amount", "idempotency_key"},
                {"account_id", "code", "is_system"},
                "0004_ledger_system_accounts",
            ),
            "BANKING_CORE_V21_PLUS_0004",
        )

    def test_unknown_revision_is_not_accepted_as_known_state(self):
        tables = {"users", "accounts", "transactions", *LEDGER_TABLES}
        self.assertEqual(
            classify(
                tables,
                {"id", "amount", "idempotency_key"},
                {"account_id"},
                "some-other-revision",
            ),
            "BANKING_CORE_V21_UNSTAMPED_OR_UNKNOWN_REVISION",
        )

    def test_partial_schema_is_unknown(self):
        tables = {"users", "accounts"}
        self.assertEqual(
            classify(tables, {"id"}, set(), None),
            "UNKNOWN_OR_PARTIAL_SCHEMA",
        )


if __name__ == "__main__":
    unittest.main()
