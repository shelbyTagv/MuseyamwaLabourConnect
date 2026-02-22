"""
Async SQLAlchemy engine and session factory for PostgreSQL.
"""

from urllib.parse import urlparse, urlunparse, parse_qs
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# asyncpg doesn't understand URL params like ?sslmode=require&channel_binding=require
# Strip ALL query params from the URL and pass SSL via connect_args instead
_db_url = settings.DATABASE_URL
_connect_args = {}

_parsed = urlparse(_db_url)
if _parsed.query:
    _params = parse_qs(_parsed.query)
    # Enable SSL if sslmode was in the URL
    if "sslmode" in _params:
        _connect_args["ssl"] = "require"
    # Rebuild URL without any query string
    _db_url = urlunparse(_parsed._replace(query=""))

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
