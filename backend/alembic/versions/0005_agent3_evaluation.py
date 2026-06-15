"""Agent 3 — create evaluations table.

Revision ID: 0005_agent3_eval
Revises: 0004_agent2_risk
Create Date: 2026-04-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_agent3_eval"
down_revision = "0004_agent2_risk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("global_score", sa.Float(), nullable=True),
        sa.Column("litigation_risk", sa.String(16), nullable=True),
        sa.Column("lnpdp_score", sa.Float(), nullable=True),
        sa.Column("gdpr_score", sa.Float(), nullable=True),
        sa.Column("iso27001_score", sa.Float(), nullable=True),
        sa.Column("iso9001_score", sa.Float(), nullable=True),
        sa.Column("active_frameworks_json", sa.Text(), nullable=True),
        sa.Column("violations_json", sa.Text(), nullable=True),
        sa.Column("missing_clauses_json", sa.Text(), nullable=True),
        sa.Column("violation_counts_json", sa.Text(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index("ix_evaluations_document_id", "evaluations", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_evaluations_document_id", table_name="evaluations")
    op.drop_table("evaluations")
