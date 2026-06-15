"""add progress tracking fields to documents

Revision ID: 0002_agent1
Revises: 0001_agent1
Create Date: 2026-03-09 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_agent1"
down_revision = "0001_agent1"
branch_labels = None
depends_on = None


def _get_document_columns() -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns("documents")}


def upgrade() -> None:
    columns = _get_document_columns()

    if "progress_percent" not in columns:
        op.add_column(
            "documents",
            sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="5"),
        )
    if "progress_stage" not in columns:
        op.add_column(
            "documents",
            sa.Column("progress_stage", sa.String(length=64), nullable=False, server_default="queued"),
        )
    if "progress_message" not in columns:
        op.add_column(
            "documents",
            sa.Column("progress_message", sa.String(length=512), nullable=True),
        )
    if "last_error" not in columns:
        op.add_column(
            "documents",
            sa.Column("last_error", sa.Text(), nullable=True),
        )
    if "finished_at" not in columns:
        op.add_column(
            "documents",
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    columns = _get_document_columns()

    if "finished_at" in columns:
        op.drop_column("documents", "finished_at")
    if "last_error" in columns:
        op.drop_column("documents", "last_error")
    if "progress_message" in columns:
        op.drop_column("documents", "progress_message")
    if "progress_stage" in columns:
        op.drop_column("documents", "progress_stage")
    if "progress_percent" in columns:
        op.drop_column("documents", "progress_percent")
