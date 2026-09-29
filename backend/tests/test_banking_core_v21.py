import unittest
from decimal import Decimal

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User, UserRole, Account, AccountType, Transaction, TransactionType
from app.models.ledger import LedgerJournal, LedgerEntry, LedgerEntryDirection
from app.models import audit as _audit_models  # noqa: F401
from app.models import baas as _baas_models  # noqa: F401
from app.services.banking_core_v21 import transfer_v21
from app.models.schemas_banking_core_v21 import TransferV21Request


class BankingCoreV21ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
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
        self.db.add_all([self.user, self.recipient])
        self.db.flush()

        self.source = Account(
            user_id=self.user.id,
            account_number="900000000001",
            account_type=AccountType.CHECKING,
            balance=1000.00,
            currency="USD",
            is_active=True,
        )
        self.destination = Account(
            user_id=self.recipient.id,
            account_number="900000000002",
            account_type=AccountType.CHECKING,
            balance=100.00,
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

        source_balance = self.db.query(Account.balance).filter(Account.id == self.source.id).scalar()
        destination_balance = self.db.query(Account.balance).filter(Account.id == self.destination.id).scalar()

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
            sum(Decimal(str(e.amount)) for e in entries if e.direction == LedgerEntryDirection.DEBIT),
            Decimal("100.00"),
        )
        self.assertEqual(
            sum(Decimal(str(e.amount)) for e in entries if e.direction == LedgerEntryDirection.CREDIT),
            Decimal("100.00"),
        )

        repeated = transfer_v21(self.db, self.user, request)
        self.assertEqual(repeated.id, first.id)
        self.db.commit()

        self.assertEqual(
            self.db.query(LedgerJournal).filter(LedgerJournal.transaction_id == first.id).count(),
            1,
        )
        self.assertEqual(
            self.db.query(Transaction).filter(Transaction.idempotency_key == key).count(),
            1,
        )


if __name__ == "__main__":
    unittest.main()
