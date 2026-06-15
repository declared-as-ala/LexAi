"""agent2 nlp_analysis table

Revision ID: 0003_agent2
Revises: 0002_agent1_progress
Create Date: 2026-04-14 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_agent2"
down_revision = "0002_agent1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nlp_analysis",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("language_confidence", sa.Float(), nullable=True),
        sa.Column("clause_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clauses_json", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_nlp_analysis_document_id", "nlp_analysis", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_nlp_analysis_document_id", table_name="nlp_analysis")
    op.drop_table("nlp_analysis")
