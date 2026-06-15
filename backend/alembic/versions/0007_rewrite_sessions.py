"""Rewrite sessions, clause decisions, exports.

Revision ID: 0007_rewrite
Revises: 0006_agent4_rec
Create Date: 2026-04-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_rewrite"
down_revision = "0006_agent4_rec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rewrite_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("final_text", sa.Text(), nullable=True),
        sa.Column("revision_metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rewrite_sessions_document_id", "rewrite_sessions", ["document_id"])
    op.create_index("ix_rewrite_sessions_status", "rewrite_sessions", ["status"])

    op.create_table(
        "rewrite_clause_decisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("recommendation_id", sa.Integer(), nullable=False),
        sa.Column("clause_id", sa.String(length=64), nullable=True),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["rewrite_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "recommendation_id", name="uq_rewrite_decision_rec"),
    )
    op.create_index("ix_rewrite_clause_decisions_session_id", "rewrite_clause_decisions", ["session_id"])
    op.create_index("ix_rewrite_clause_decisions_recommendation_id", "rewrite_clause_decisions", ["recommendation_id"])
    op.create_index("ix_rewrite_clause_decisions_clause_id", "rewrite_clause_decisions", ["clause_id"])

    op.create_table(
        "rewrite_exports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("meta_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["rewrite_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rewrite_exports_session_id", "rewrite_exports", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_rewrite_exports_session_id", table_name="rewrite_exports")
    op.drop_table("rewrite_exports")
    op.drop_index("ix_rewrite_clause_decisions_clause_id", table_name="rewrite_clause_decisions")
    op.drop_index("ix_rewrite_clause_decisions_recommendation_id", table_name="rewrite_clause_decisions")
    op.drop_index("ix_rewrite_clause_decisions_session_id", table_name="rewrite_clause_decisions")
    op.drop_table("rewrite_clause_decisions")
    op.drop_index("ix_rewrite_sessions_status", table_name="rewrite_sessions")
    op.drop_index("ix_rewrite_sessions_document_id", table_name="rewrite_sessions")
    op.drop_table("rewrite_sessions")
