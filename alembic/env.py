from __future__ import annotations

import os
import sys
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine.url import make_url, URL
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
# Load .env early so DATABASE_URL / DB_* are available
load_dotenv()

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

def _redact_url(u: URL | str) -> str:
    """Return DSN with password redacted for logs."""
    try:
        url = make_url(str(u))
        return str(url)
    except Exception:
        return str(u)

def _env(name: str, default: str = "") -> str:
    v = os.getenv(name, default)
    return v

# Helpful environment echoes
logger.info("Python: %s", sys.version.replace("\n", " "))
logger.info("CWD: %s", os.getcwd())
logger.info("PYTHONPATH: %s", os.getenv("PYTHONPATH", ""))
logger.info("ALembic INI section: %s", config.config_ini_section)

# Prefer app settings if available; fall back to raw env
db_url_raw = os.getenv("DATABASE_URL")
if not db_url_raw:
    logger.error("DATABASE_URL is not set. Ensure .env is loaded or env var exported.")
    raise RuntimeError("DATABASE_URL is not set")

# Normalize async DSN -> sync (Alembic uses sync engine)
try:
    # Convert asyncpg URL to psycopg2 URL
    if "+asyncpg" in db_url_raw:
        db_url_raw = db_url_raw.replace("+asyncpg", "")
    
    # Force IPv4 for localhost
    if "localhost" in db_url_raw and os.getenv("ALEMBIC_FORCE_IPV4", "1") == "1":
        db_url_raw = db_url_raw.replace("localhost", "127.0.0.1")
    
    parsed = make_url(db_url_raw)
except Exception as e:
    logger.exception("Failed to parse DATABASE_URL: %s", e)
    raise

config.set_main_option("sqlalchemy.url", db_url_raw)

# Log effective DB URL (redacted)
logger.info("Alembic effective DB URL: %s", _redact_url(parsed))
logger.info(
    "DB host=%s port=%s db=%s user=%s",
    parsed.host, parsed.port, parsed.database, parsed.username
)

# ---------------------------------------------------------------------------
# Import application metadata (models)
# ---------------------------------------------------------------------------
try:
    from app.db.base import Base  # Base.metadata with naming conventions
    from app.db.models import *   # noqa: F401,F403 (import to populate metadata)
except Exception as e:
    logger.exception("Failed to import app metadata/models. Check PYTHONPATH and package structure. Error: %s", e)
    raise

target_metadata = Base.metadata
if not target_metadata.tables:
    logger.warning("No tables found on target_metadata. Autogenerate may create an empty revision.")

# ---------------------------------------------------------------------------
# Migration routines
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    logger.info("Running offline migrations against: %s", _redact_url(url))

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    logger.info("Running online migrations...")
    connectable = None
    try:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )

        # Preflight: log a simple connect attempt (SQLAlchemy will raise clearly)
        with connectable.connect() as connection:
            logger.info("DB connection established OK to: %s", _redact_url(parsed))
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
                include_schemas=False,
            )
            with context.begin_transaction():
                context.run_migrations()
            logger.info("Migrations completed successfully.")
    except Exception as e:
        logger.exception("Alembic online migration failed: %s", e)
        raise
    finally:
        if connectable is not None:
            try:
                connectable.dispose()
            except Exception:
                pass


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
