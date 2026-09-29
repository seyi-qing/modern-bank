import os
import unittest
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.deps import get_current_user
from app.main import app
from app.models.user import User, Account, Transaction
from app.models.ledger import LedgerJournal, LedgerEntry, LedgerEntryDirection
from app.models import audit as _audit_models  # noqa: F401
from app.models import baas as _baas_models  # noqa: F401
from app.models import ledger as _ledger_models  # noqa: F401


class StagingApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.getenv("MODERNBANK_STAGING_TEST") != "1":
            raise RuntimeError("Refusing to run: MODERNBANK_STAGING_TEST must be 1")

        database_url = os.getenv("DATABASE_URL", "")
        if not database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise RuntimeError("Refusing to run: staging test requires PostgreSQL DATABASE_URL")

        if "neon.tech" not in database_url:
            raise RuntimeError("Refusing to run: DATABASE_URL is not a Neon staging connection")

        cls.engine = create_engine(database_url, pool_pre_ping=True)
        cls.Session = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False)

        with cls.Session() as db:
            cls.user1 = db.query(User).filter(User.id == 1).one()
            cls.user2 = db.query(User).filter(User.id == 2).one()
            cls.account1 = db.query(Account).filter(Account.id == 1).one()
            cls.account2 = db.query(Account).filter(Account.id == 2).one()

        if cls.account1.user_id != cls.user1.id or cls.account2.user_id != cls.user2.id:
            raise RuntimeError("Refusing to run: expected isolated staging account ownership was not found")
        if cls.account1.currency != "USD" or cls.account2.currency != "USD":
            raise RuntimeError("Refusing to run: expected USD staging accounts were not found")

        app.dependency_overrides[get_current_user] = lambda: cls.user1
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.client.close()
        cls.engine.dispose()

    def test_http_transfer_idempotency_ledger_and_balance_round_trip(self):
        with self.Session() as db:
            before_1 = Decimal(str(db.query(Account.balance).filter(Account.id == 1).scalar()))
            before_2 = Decimal(str(db.query(Account.balance).filter(Account.id == 2).scalar()))

        key = f"ci-staging-roundtrip-{os.getenv('GITHUB_RUN_ID', 'local')}"
        payload = {
            "from_account_id": 1,
            "to_account_number": self.account2.account_number,
            "amount": "1.00",
            "currency": "USD",
            "description": "CI staging application test",
            "idempotency_key": key,
        }

        response = self.client.post(
            "/api/v1/banking/v2/transfer",
            json=payload,
            headers={"Idempotency-Key": key},
        )
        self.assertEqual(response.status_code, 200, response.text)
        first = response.json()
        self.assertEqual(first["status"], "COMPLETED")
        transaction_id = first["id"]

        repeated = self.client.post(
            "/api/v1/banking/v2/transfer",
            json=payload,
            headers={"Idempotency-Key": key},
        )
        self.assertEqual(repeated.status_code, 200, repeated.text)
        self.assertEqual(repeated.json()["id"], transaction_id)

        with self.Session() as db:
            source = db.query(Account).filter(Account.id == 1).one()
            destination = db.query(Account).filter(Account.id == 2).one()
            self.assertEqual(Decimal(str(source.balance)), before_1 - Decimal("1.00"))
            self.assertEqual(Decimal(str(destination.balance)), before_2 + Decimal("1.00"))

            journal = db.query(LedgerJournal).filter(
                LedgerJournal.transaction_id == transaction_id
            ).one()
            entries = db.query(LedgerEntry).filter(
                LedgerEntry.journal_id == journal.id
            ).all()
            self.assertEqual(len(entries), 2)
            self.assertEqual(
                sum(Decimal(str(e.amount)) for e in entries if e.direction == LedgerEntryDirection.DEBIT),
                Decimal("1.00"),
            )
            self.assertEqual(
                sum(Decimal(str(e.amount)) for e in entries if e.direction == LedgerEntryDirection.CREDIT),
                Decimal("1.00"),
            )
            self.assertEqual(
                db.query(Transaction).filter(Transaction.idempotency_key == key).count(),
                1,
            )

        # Reverse the test transfer through the same HTTP application path.
        app.dependency_overrides[get_current_user] = lambda: self.user2
        reverse_key = f"ci-staging-roundtrip-reverse-{os.getenv('GITHUB_RUN_ID', 'local')}"
        reverse_payload = {
            "from_account_id": 2,
            "to_account_number": self.account1.account_number,
            "amount": "1.00",
            "currency": "USD",
            "description": "CI staging application test reversal",
            "idempotency_key": reverse_key,
        }
        reverse = self.client.post(
            "/api/v1/banking/v2/transfer",
            json=reverse_payload,
            headers={"Idempotency-Key": reverse_key},
        )
        self.assertEqual(reverse.status_code, 200, reverse.text)

        with self.Session() as db:
            after_1 = Decimal(str(db.query(Account.balance).filter(Account.id == 1).scalar()))
            after_2 = Decimal(str(db.query(Account.balance).filter(Account.id == 2).scalar()))
            self.assertEqual(after_1, before_1)
            self.assertEqual(after_2, before_2)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "healthy")
        self.assertEqual(response.json()["banking_core"], "v2.1")


if __name__ == "__main__":
    unittest.main()
