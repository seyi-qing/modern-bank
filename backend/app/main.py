"""ModernBank API - FastAPI entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import DATABASE_URL
from app.models import audit as audit_models  # noqa: F401
from app.models import baas as baas_models  # noqa: F401
from app.models import ledger as ledger_models  # noqa: F401
from app.models import card_request as card_request_models  # noqa: F401
from app.routers import admin, admin_core_v21, auth, baas, banking, banking_core_v21, cards, notifications, payments

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Production databases are created and upgraded by Alembic migrations.
    # Demo/admin/customer seeding must never run automatically at startup.
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ModernBank API. Banking Core v2.1 + control-plane RBAC.",
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
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs", "status": "operational", "database": _db_kind(), "banking_core": "v2.1"}

@app.get("/health")
def health():
    return {"status": "healthy", "database": _db_kind(), "banking_core": "v2.1"}
