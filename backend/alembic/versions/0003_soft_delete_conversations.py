"""preserve conversation data when deleted

Revision ID: 0003_soft_delete_conversations
Revises: 0002_conversation_actions
Create Date: 2026-08-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_soft_delete_conversations"
down_revision = "0002_conversation_actions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("conversations", "is_deleted", server_default=None)


def downgrade() -> None:
    op.drop_column("conversations", "is_deleted")
