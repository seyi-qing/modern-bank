"""
ModernBank API - FastAPI entrypoint.
Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal, DATABASE_URL
from app.models.user import User, UserRole, Account, AccountType, Card, CardType, CardStatus
from app.models import baas as baas_models  # noqa: F401
from app.core.security import get_password_hash
from app.routers import auth, banking, admin, cards, notifications, payments, baas
import random
import string
from datetime import datetime, timezone


def generate_account_number() -> str:
    return "".join(random.choices(string.digits, k=12))


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

            from app.models.baas import (
                DepositAccount, DepositProduct, AccountStatus,
                CreditAccount, CreditAccountStatus,
            )
            dep = DepositAccount(
                user_id=demo.id,
                name="Alex Rivera Checking",
                status=AccountStatus.OPEN,
                deposit_product=DepositProduct.CHECKING,
                routing_number="021000021",
                account_number="1000000002",
                currency="USD",
                balance=10000.00,
                hold=0.0,
                available=10000.00,
                tags={"purpose": "checking"},
                is_wallet=False,
            )
            wallet = DepositAccount(
                user_id=demo.id,
                name="Operating Wallet (FBO)",
                status=AccountStatus.OPEN,
                deposit_product=DepositProduct.WALLET,
                routing_number="021000021",
                account_number="9000000001",
                currency="USD",
                balance=2500.00,
                hold=0.0,
                available=2500.00,
                tags={"purpose": "wallet"},
                is_wallet=True,
            )
            credit = CreditAccount(
                user_id=demo.id,
                name="Alex Revolving",
                status=CreditAccountStatus.OPEN,
                credit_terms="credit_terms_1",
                currency="USD",
                credit_limit=5000.00,
                balance=0.0,
                hold=0.0,
                available=5000.00,
            )
            db.add_all([dep, wallet, credit])

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
    description="ModernBank – AI-driven cloud-native banking API demo.",
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
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(banking.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)
app.include_router(cards.router, prefix=settings.API_PREFIX)
app.include_router(notifications.router, prefix=settings.API_PREFIX)
app.include_router(payments.router, prefix=settings.API_PREFIX)
app.include_router(baas.router, prefix=settings.API_PREFIX)


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
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": _db_kind(),
        "hint": (
            "Set DATABASE_URL to a Neon postgresql:// string on Vercel if you see login 200 then /me 401"
            if _db_kind() == "sqlite"
            else "ok"
        ),
    }
