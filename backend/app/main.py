"""
MuseyamwaLabourConnect – FastAPI Application Entry Point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.routes import auth, users, jobs, tokens, payments, locations, messages, offers, ratings, notifications, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables, seed admin, and optionally seed sample data on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ensure new columns exist on already-created tables (safe migrations)
    await ensure_columns()

    # Seed admin user
    await seed_admin()
    # Auto-seed sample data (safe for free-tier deploys with no shell access)
    if settings.AUTO_SEED:
        try:
            from app.seed import seed
            await seed()
        except Exception as e:
            print(f"Auto-seed skipped or failed: {e}")
    yield


async def ensure_columns():
    """
    Add columns that may be missing from existing tables.
    Uses IF NOT EXISTS so it's safe to run repeatedly.
    """
    from sqlalchemy import text

    migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_otp VARCHAR(10)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_otp_expires TIMESTAMP",
    ]

    async with engine.begin() as conn:
        for sql in migrations:
            try:
                await conn.execute(text(sql))
            except Exception as e:
                print(f"Migration note: {e}")
    print("✅ Column migrations checked.")


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

# ── CORS Middleware ────────────────────────────────────────────
# Must be added BEFORE routes so preflight OPTIONS requests are handled

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
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
