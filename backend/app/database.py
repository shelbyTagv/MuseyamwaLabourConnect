"""
Async SQLAlchemy engine and session factory for PostgreSQL.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# asyncpg doesn't understand ?sslmode=require — it needs ssl="require" in connect_args
_db_url = settings.DATABASE_URL
_connect_args = {}
if "sslmode=" in _db_url:
    _db_url = _db_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
    _connect_args["ssl"] = "require"

engine = create_async_engine(_db_url, echo=False, pool_pre_ping=True, connect_args=_connect_args)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db():
    """FastAPI dependency – yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
