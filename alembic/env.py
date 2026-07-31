import sys
import os
from dotenv import load_dotenv

# Add the root directory to sys.path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
load_dotenv()

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import Base and models
from app.db.session import Base
from app.users.models import *
from app.safe_points.models import *
from app.reports.models import *
from app.trips.models import *
from app.emergency.models import *
from app.system.models import *
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def get_url():
    # Supabase uses session pooler (port 5432) for migrations, and transaction pooler (6543) for app.
    return os.environ.get("DIRECT_URL", settings.DATABASE_URL)

def include_name(name, type_, parent_names):
    if type_ == "schema":
        # Only include the public schema, ignore Supabase internal schemas (auth, storage, realtime, vault)
        return name in [None, "public"]
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
