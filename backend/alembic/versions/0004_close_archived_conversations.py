"""convert archived conversations to closed conversations

Revision ID: 0004_close_conversations
Revises: 0003_soft_delete_conversations
Create Date: 2026-08-10 00:00:00.000000
"""

from alembic import op


revision = "0004_close_conversations"
down_revision = "0003_soft_delete_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE conversations SET status = 'closed' WHERE is_archived = true")


def downgrade() -> None:
    op.execute("UPDATE conversations SET is_archived = true WHERE status = 'closed'")
