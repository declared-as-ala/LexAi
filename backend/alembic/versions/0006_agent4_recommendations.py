"""Agent 4 — create recommendations table.

Revision ID: 0006_agent4_rec
Revises: 0005_agent3_eval
Create Date: 2026-04-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_agent4_rec"
down_revision = "0005_agent3_eval"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("violation_id", sa.String(length=64), nullable=True),
        sa.Column("clause_id", sa.String(length=64), nullable=True),
        sa.Column("violation_rule_id", sa.String(length=128), nullable=True),
        sa.Column("framework", sa.String(length=32), nullable=True),
        sa.Column("article", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("issue_description", sa.Text(), nullable=True),
        sa.Column("recommendation_text", sa.Text(), nullable=True),
        sa.Column("rewritten_clause", sa.Text(), nullable=True),
        sa.Column("legal_rationale", sa.Text(), nullable=True),
        sa.Column("generated_by", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recommendations_document_id", "recommendations", ["document_id"])
    op.create_index("ix_recommendations_violation_id", "recommendations", ["violation_id"])
    op.create_index("ix_recommendations_violation_rule_id", "recommendations", ["violation_rule_id"])


def downgrade() -> None:
    op.drop_index("ix_recommendations_violation_rule_id", table_name="recommendations")
    op.drop_index("ix_recommendations_violation_id", table_name="recommendations")
    op.drop_index("ix_recommendations_document_id", table_name="recommendations")
    op.drop_table("recommendations")
