"""
MuseyamwaLabourConnect – FastAPI Application Entry Point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.routes import auth, users, jobs, tokens, payments, locations, messages, offers, ratings, notifications, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed admin on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed admin user
    await seed_admin()
    yield


async def seed_admin():
    """Create the admin user from env vars if not exists."""
    from sqlalchemy import select
    from app.models.user import User, UserRole, AdminRole
    from app.models.profile import Profile
    from app.models.token import TokenWallet
    from app.services.auth import hash_password

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        if not result.scalar_one_or_none():
            admin_user = User(
                email=settings.ADMIN_EMAIL,
                phone=settings.ADMIN_PHONE,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                full_name="System Admin",
                role=UserRole.ADMIN,
                admin_role=AdminRole.SUPER_ADMIN,
                is_verified=True,
                is_active=True,
            )
            db.add(admin_user)
            await db.flush()
            db.add(Profile(user_id=admin_user.id))
            db.add(TokenWallet(user_id=admin_user.id, balance=9999))
            await db.commit()


app = FastAPI(
    title=settings.APP_NAME,
    description="A dynamic, tokenized, real-time job and labour marketplace for Zimbabwe.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ─────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes ─────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(jobs.router, prefix=API_PREFIX)
app.include_router(tokens.router, prefix=API_PREFIX)
app.include_router(payments.router, prefix=API_PREFIX)
app.include_router(locations.router, prefix=API_PREFIX)
app.include_router(messages.router, prefix=API_PREFIX)
app.include_router(offers.router, prefix=API_PREFIX)
app.include_router(ratings.router, prefix=API_PREFIX)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
