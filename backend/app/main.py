"""
ModernBank API - FastAPI entrypoint.
Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal, DATABASE_URL
from app.models.user import (
    User,
    UserRole,
    Account,
    AccountType,
    Card,
    CardType,
    CardStatus,
    Transaction,
    TransactionType,
    TransactionStatus,
    Notification,
    SavingsGoal,
)
from app.models import baas as baas_models  # noqa: F401
from app.models import ledger as ledger_models  # noqa: F401 — Banking Core v2.1
from app.models import audit as audit_models  # noqa: F401 — admin audit trail
from app.core.security import get_password_hash
from app.routers import auth, banking, admin, cards, notifications, payments, baas
from app.routers import banking_core_v21, admin_core_v21
import random
import string
from datetime import datetime, timezone, timedelta


def generate_account_number() -> str:
    return "".join(random.choices(string.digits, k=12))


def _seed_demo_activity(db, demo: User, checking: Account):
    """Idempotent sample activity for the demo customer."""
    now = datetime.now(timezone.utc)

    tx_count = db.query(Transaction).filter(Transaction.user_id == demo.id).count()
    if tx_count == 0:
        samples = [
            Transaction(
                user_id=demo.id,
                account_id=checking.id,
                amount=3200.0,
                currency="USD",
                type=TransactionType.DEPOSIT,
                status=TransactionStatus.COMPLETED,
                description="Payroll — Acme Corp",
                reference="TXN-PAYROLL001",
                is_flagged=False,
                fraud_score=0.0,
                created_at=now - timedelta(days=12),
            ),
            Transaction(
                user_id=demo.id,
                account_id=checking.id,
                amount=84.5,
                currency="USD",
                type=TransactionType.TRANSFER_OUT,
                status=TransactionStatus.COMPLETED,
                description="Transfer to •••• 2201",
                reference="TXN-OUT000002",
                is_flagged=False,
                fraud_score=0.12,
                created_at=now - timedelta(days=5),
            ),
            Transaction(
                user_id=demo.id,
                account_id=checking.id,
                amount=45.99,
                currency="USD",
                type=TransactionType.PAYMENT,
                status=TransactionStatus.COMPLETED,
                description="Card · Everyday · CLOUDFLARE",
                reference="TXN-CARD000004",
                is_flagged=False,
                fraud_score=0.05,
                created_at=now - timedelta(days=3),
            ),
            Transaction(
                user_id=demo.id,
                account_id=checking.id,
                amount=2500.0,
                currency="USD",
                type=TransactionType.TRANSFER_OUT,
                status=TransactionStatus.FLAGGED,
                description="Large transfer — review",
                reference="TXN-FLAG000003",
                is_flagged=True,
                fraud_score=0.72,
                created_at=now - timedelta(hours=6),
            ),
        ]
        db.add_all(samples)

    goal_count = db.query(SavingsGoal).filter(SavingsGoal.user_id == demo.id).count()
    if goal_count == 0:
        db.add_all(
            [
                SavingsGoal(
                    user_id=demo.id,
                    name="Emergency fund",
                    target_amount=10000.0,
                    current_amount=4200.0,
                    deadline=now + timedelta(days=180),
                ),
            ]
        )


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@modernbank.dev").first()
        if not admin:
            admin = User(
                email="admin@modernbank.dev",
                hashed_password=get_password_hash("Admin123!"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                kyc_status="verified",
            )
            db.add(admin)
            db.flush()
            acc = Account(
                user_id=admin.id,
                account_number=generate_account_number(),
                account_type=AccountType.CHECKING,
                balance=1000000.0,
            )
            db.add(acc)

        demo = db.query(User).filter(User.email == "demo@modernbank.dev").first()
        if not demo:
            demo = User(
                email="demo@modernbank.dev",
                hashed_password=get_password_hash("Demo1234!"),
                full_name="Alex Rivera",
                phone="+1-555-0100",
                role=UserRole.CUSTOMER,
                is_active=True,
                is_verified=True,
                kyc_status="verified",
            )
            db.add(demo)
            db.flush()

            checking = Account(
                user_id=demo.id,
                account_number=generate_account_number(),
                account_type=AccountType.CHECKING,
                balance=4250.75,
            )
            savings = Account(
                user_id=demo.id,
                account_number=generate_account_number(),
                account_type=AccountType.SAVINGS,
                balance=12500.00,
            )
            db.add_all([checking, savings])
            db.flush()

            now = datetime.now(timezone.utc)
            card = Card(
                user_id=demo.id,
                account_id=checking.id,
                card_number_masked="•••• •••• •••• 4242",
                last_four="4242",
                card_type=CardType.VIRTUAL,
                status=CardStatus.ACTIVE,
                expiry_month=now.month,
                expiry_year=now.year + 3,
                spending_limit=2500.0,
                label="Everyday",
            )
            db.add(card)

        if demo:
            checking = (
                db.query(Account)
                .filter(Account.user_id == demo.id, Account.account_type == AccountType.CHECKING)
                .first()
            )
            if checking:
                _seed_demo_activity(db, demo, checking)

        db.commit()
        print("Database seeded")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_database()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ModernBank – AI-driven cloud-native banking API demo. Banking Core v2.1 ledger enabled.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

origins = settings.cors_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Idempotency-Key"],
)

app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(banking.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)
app.include_router(cards.router, prefix=settings.API_PREFIX)
app.include_router(notifications.router, prefix=settings.API_PREFIX)
app.include_router(payments.router, prefix=settings.API_PREFIX)
app.include_router(baas.router, prefix=settings.API_PREFIX)
# Banking Core v2.1 — double-entry transfers + admin reconciliation
app.include_router(banking_core_v21.router, prefix=settings.API_PREFIX)
app.include_router(admin_core_v21.router, prefix=settings.API_PREFIX)


def _db_kind() -> str:
    u = DATABASE_URL.lower()
    if u.startswith("postgresql"):
        return "postgresql"
    if u.startswith("sqlite"):
        return "sqlite"
    return "other"


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "operational",
        "database": _db_kind(),
        "banking_core": "v2.1",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": _db_kind(),
        "banking_core": "v2.1",
    }
