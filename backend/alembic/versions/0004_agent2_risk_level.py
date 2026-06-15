"""agent2 risk_level and compliance_score columns

Revision ID: 0004_agent2_risk
Revises: 0003_agent2
Create Date: 2026-04-20 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_agent2_risk"
down_revision = "0003_agent2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("nlp_analysis", sa.Column("risk_level", sa.String(16), nullable=True))
    op.add_column("nlp_analysis", sa.Column("compliance_score", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("nlp_analysis", "compliance_score")
    op.drop_column("nlp_analysis", "risk_level")
