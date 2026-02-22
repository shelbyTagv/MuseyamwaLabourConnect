"""
Alembic environment configuration for async SQLAlchemy.
"""

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import asyncio

from app.config import settings
from app.database import Base

# Import all models so they're registered with Base.metadata
from app.models.user import User
from app.models.profile import Profile
from app.models.job import Job
from app.models.offer import Offer
from app.models.token import TokenWallet, TokenTransaction
from app.models.payment import Payment
from app.models.location import Location
from app.models.rating import Rating
from app.models.message import Message
from app.models.notification import Notification
from app.models.audit_log import AuditLog

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL_SYNC
    context.configure(
        url=url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
