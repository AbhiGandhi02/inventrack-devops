from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app import models  # noqa: F401  registers the tables
from app.database import Base
from app.settings import get_settings

if context.config.config_file_name:
    fileConfig(context.config.config_file_name)

DATABASE_URL = get_settings().database_url
target_metadata = Base.metadata


def run_offline() -> None:
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_online() -> None:
    engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_offline() if context.is_offline_mode() else run_online()
