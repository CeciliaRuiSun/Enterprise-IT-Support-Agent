"""add conversation pin and archive flags

Revision ID: 0002_conversation_actions
Revises: 0001_initial
Create Date: 2026-08-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_conversation_actions"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "conversations",
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("conversations", "is_pinned", server_default=None)
    op.alter_column("conversations", "is_archived", server_default=None)


def downgrade() -> None:
    op.drop_column("conversations", "is_archived")
    op.drop_column("conversations", "is_pinned")
