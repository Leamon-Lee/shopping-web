"""Alembic environment configuration for online_shopping."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from online_shopping.config import settings
from online_shopping.models import Base

# Import all models so Base.metadata is complete
import online_shopping.models.account  # noqa
import online_shopping.models.address  # noqa
import online_shopping.models.cart  # noqa
import online_shopping.models.category  # noqa
import online_shopping.models.order  # noqa
import online_shopping.models.payment  # noqa
import online_shopping.models.product  # noqa
import online_shopping.models.product_image  # noqa
import online_shopping.models.product_variant  # noqa
import online_shopping.models.review  # noqa
import online_shopping.models.shipment  # noqa
import online_shopping.models.shop  # noqa
import online_shopping.models.wishlist  # noqa

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
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
