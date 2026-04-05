import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from src.infrastructure.database.models import Base

# Alembic Config object
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata для autogenerate
target_metadata = Base.metadata


def get_url() -> str:
    """URL всегда берётся из переменных окружения."""
    return (
        os.environ.get("DATABASE_URL")
        or (
            f"postgresql+asyncpg://"
            f"{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
            f"@{os.environ.get('POSTGRES_HOST', 'localhost')}:"
            f"{os.environ.get('POSTGRES_PORT', '5432')}/"
            f"{os.environ['POSTGRES_DB']}"
        )
    )


def run_migrations_offline() -> None:
    """Оффлайн-режим: генерирует SQL без подключения к БД."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Async-режим: подключается к PostgreSQL через asyncpg."""
    connectable = create_async_engine(get_url(), echo=False)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
