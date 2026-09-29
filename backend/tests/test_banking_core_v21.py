import unittest
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import (
    User,
    UserRole,
    Account,
    AccountType,
    Transaction,
    TransactionType,
    TransactionStatus,
)
from app.models.ledger import LedgerJournal, LedgerEntry, LedgerEntryDirection
from app.models import audit as _audit_models  # noqa: F401
from app.models import baas as _baas_models  # noqa: F401
from app.services.banking_core_v21 import transfer_v21, admin_review_transfer
from app.models.schemas_banking_core_v21 import TransferV21Request
from app.services.ledger_service import reconcile_account


class BankingCoreV21ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.db = self.Session()
        self.user = User(
            email="ci-customer@example.test",
            hashed_password="test",
            full_name="CI Customer",
            role=UserRole.CUSTOMER,
            is_active=True,
        )
        self.recipient = User(
            email="ci-recipient@example.test",
            hashed_password="test",
            full_name="CI Recipient",
            role=UserRole.CUSTOMER,
            is_active=True,
        )
        self.admin = User(
            email="ci-admin@example.test",
            hashed_password="test",
            full_name="CI Admin",
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.db.add_all([self.user, self.recipient, self.admin])
        self.db.flush()

        self.source = Account(
            user_id=self.user.id,
            account_number="900000000001",
            account_type=AccountType.CHECKING,
            balance=Decimal("1000.00"),
            currency="USD",
            is_active=True,
        )
        self.destination = Account(
            user_id=self.recipient.id,
            account_number="900000000002",
            account_type=AccountType.CHECKING,
            balance=Decimal("100.00"),
            currency="USD",
            is_active=True,
        )
        self.db.add_all([self.source, self.destination])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_transfer_posts_balanced_ledger_and_is_idempotent(self):
        key = "ci-idempotency-key-001"
        request = TransferV21Request(
            from_account_id=self.source.id,
            to_account_number=self.destination.account_number,
            amount=Decimal("100.00"),
            currency="USD",
            description="CI transfer",
            idempotency_key=key,
        )

        first = transfer_v21(self.db, self.user, request)
        self.db.commit()

        source_balance = (
            self.db.query(Account.balance).filter(Account.id == self.source.id).scalar()
        )
        destination_balance = (
            self.db.query(Account.balance)
            .filter(Account.id == self.destination.id)
            .scalar()
        )

        self.assertEqual(Decimal(str(source_balance)), Decimal("900.00"))
        self.assertEqual(Decimal(str(destination_balance)), Decimal("200.00"))

        journal = (
            self.db.query(LedgerJournal)
            .filter(LedgerJournal.transaction_id == first.id)
            .one()
        )
        entries = (
            self.db.query(LedgerEntry)
            .filter(LedgerEntry.journal_id == journal.id)
            .order_by(LedgerEntry.id)
            .all()
        )
        self.assertEqual(len(entries), 2)
        self.assertEqual(
            sum(
                Decimal(str(e.amount))
                for e in entries
                if e.direction == LedgerEntryDirection.DEBIT
            ),
            Decimal("100.00"),
        )
        self.assertEqual(
            sum(
                Decimal(str(e.amount))
                for e in entries
                if e.direction == LedgerEntryDirection.CREDIT
            ),
            Decimal("100.00"),
        )

        repeated = transfer_v21(self.db, self.user, request)
        self.assertEqual(repeated.id, first.id)
        self.db.commit()

        self.assertEqual(
            self.db.query(LedgerJournal)
            .filter(LedgerJournal.transaction_id == first.id)
            .count(),
            1,
        )
        self.assertEqual(
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == self.user.id,
                Transaction.idempotency_key == key,
            )
            .count(),
            1,
        )

        recon = reconcile_account(self.db, self.source.id)
        self.assertTrue(recon["balanced"])

    def test_two_users_may_reuse_same_idempotency_key(self):
        """Per-user scope: identical client keys across users must not collide."""
        shared_key = "shared-client-key-abcdef"
        # Give recipient a funded account as source for second user transfer
        self.destination.balance = Decimal("500.00")
        self.db.commit()

        r1 = TransferV21Request(
            from_account_id=self.source.id,
            to_account_number=self.destination.account_number,
            amount=Decimal("10.00"),
            currency="USD",
            description="user1",
            idempotency_key=shared_key,
        )
        t1 = transfer_v21(self.db, self.user, r1)
        self.db.commit()

        r2 = TransferV21Request(
            from_account_id=self.destination.id,
            to_account_number=self.source.account_number,
            amount=Decimal("5.00"),
            currency="USD",
            description="user2",
            idempotency_key=shared_key,
        )
        t2 = transfer_v21(self.db, self.recipient, r2)
        self.db.commit()

        self.assertNotEqual(t1.id, t2.id)
        self.assertEqual(t1.idempotency_key, t2.idempotency_key)
        self.assertEqual(t1.user_id, self.user.id)
        self.assertEqual(t2.user_id, self.recipient.id)

    def test_flagged_transfer_approve_keeps_recon_ok(self):
        # Force high amount to trip fraud threshold
        self.source.balance = Decimal("30000.00")
        self.db.commit()

        req = TransferV21Request(
            from_account_id=self.source.id,
            to_account_number=self.destination.account_number,
            amount=Decimal("25000.00"),
            currency="USD",
            description="Large transfer — review",
            idempotency_key="flag-key-review-001234",
        )
        tx = transfer_v21(self.db, self.user, req)
        self.db.commit()
        self.assertTrue(tx.is_flagged)
        self.assertEqual(tx.status, TransactionStatus.FLAGGED)

        # Book balance unchanged until approve
        bal = self.db.query(Account.balance).filter(Account.id == self.source.id).scalar()
        self.assertEqual(Decimal(str(bal)), Decimal("30000.00"))

        reviewed = admin_review_transfer(
            self.db, tx.id, "approve", "CI verified large transfer", self.admin
        )
        self.db.commit()
        self.assertEqual(reviewed.status, TransactionStatus.COMPLETED)
        self.assertFalse(reviewed.is_flagged)

        recon_src = reconcile_account(self.db, self.source.id)
        recon_dst = reconcile_account(self.db, self.destination.id)
        self.assertTrue(recon_src["balanced"], recon_src)
        self.assertTrue(recon_dst["balanced"], recon_dst)


if __name__ == "__main__":
    unittest.main()
