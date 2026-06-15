"""Migration bootstrap helper for container startup.

This handles the transition from the earlier `create_all`-based setup to
Alembic-managed migrations:

- fresh database -> `alembic upgrade head`
- legacy database with existing Agent 1 tables but no `alembic_version`
  -> `alembic stamp head`
- partially created legacy schema -> fail fast with a clear error
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.core.logging import get_logger
from app.db.session import engine

logger = get_logger(__name__)

LEGACY_AGENT1_TABLES = {"users", "documents", "extractions"}


def _get_columns(table_name: str) -> set[str]:
    """Return the current column names for a table."""
    with engine.connect() as connection:
        return {column["name"] for column in inspect(connection).get_columns(table_name)}


def _repair_legacy_agent1_schema() -> None:
    """Patch the pre-Alembic Agent 1 schema to match the current model shape."""
    document_columns = _get_columns("documents")

    missing_document_columns = {
        "task_id": "ALTER TABLE documents ADD COLUMN task_id VARCHAR(255)",
        "progress_percent": "ALTER TABLE documents ADD COLUMN progress_percent INTEGER DEFAULT 5 NOT NULL",
        "progress_stage": "ALTER TABLE documents ADD COLUMN progress_stage VARCHAR(64) DEFAULT 'queued' NOT NULL",
        "progress_message": "ALTER TABLE documents ADD COLUMN progress_message VARCHAR(512)",
        "last_error": "ALTER TABLE documents ADD COLUMN last_error TEXT",
        "finished_at": "ALTER TABLE documents ADD COLUMN finished_at TIMESTAMP WITH TIME ZONE",
    }

    for column_name, statement in missing_document_columns.items():
        if column_name in document_columns:
            continue
        logger.info(
            "repairing_legacy_schema",
            extra={"extra": {"table": "documents", "column": column_name}},
        )
        with engine.begin() as connection:
            connection.execute(text(statement))


def _get_alembic_config() -> Config:
    """Load Alembic config from the backend root."""
    backend_root = Path(__file__).resolve().parents[2]
    return Config(str(backend_root / "alembic.ini"))


def run_startup_migrations() -> None:
    """Apply or stamp migrations depending on the current schema state."""
    config = _get_alembic_config()

    with engine.connect() as connection:
        existing_tables = set(inspect(connection).get_table_names())

    has_alembic_version = "alembic_version" in existing_tables
    legacy_present = existing_tables & LEGACY_AGENT1_TABLES

    # Repair legacy Agent 1 schema drift regardless of whether Alembic has
    # already been stamped. This covers databases that were stamped in an
    # earlier broken run but still miss newer columns such as `task_id`.
    if "documents" in existing_tables:
        _repair_legacy_agent1_schema()

    if has_alembic_version:
        logger.info("running_alembic_upgrade", extra={"extra": {"mode": "upgrade"}})
        command.upgrade(config, "head")
        return

    if legacy_present == LEGACY_AGENT1_TABLES:
        logger.info(
            "stamping_legacy_schema_then_upgrading",
            extra={"extra": {"mode": "stamp_then_upgrade", "tables": sorted(legacy_present)}},
        )
        # Legacy Agent 1 databases were created without Alembic.
        # Stamp at the last Agent 1 revision, then run upgrades so Agent 2/3
        # tables (e.g., nlp_analysis/evaluations) are actually created.
        command.stamp(config, "0002_agent1")
        command.upgrade(config, "head")
        return

    if legacy_present:
        raise RuntimeError(
            "Partial legacy schema detected. Existing tables: "
            f"{sorted(legacy_present)}. "
            "Please reset the database or complete the migration manually."
        )

    logger.info("running_alembic_upgrade", extra={"extra": {"mode": "upgrade_fresh"}})
    command.upgrade(config, "head")


if __name__ == "__main__":
    run_startup_migrations()
