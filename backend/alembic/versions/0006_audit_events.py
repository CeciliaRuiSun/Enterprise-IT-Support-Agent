"""add append-only audit events

Revision ID: 0006_audit_events
Revises: 0005_ticket_numbers
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "0006_audit_events"
down_revision = "0005_ticket_numbers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("event_metadata", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index(op.f("ix_audit_events_request_id"), "audit_events", ["request_id"], unique=False)
    op.create_index(op.f("ix_audit_events_actor_id"), "audit_events", ["actor_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_events_actor_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_request_id"), table_name="audit_events")
    op.drop_table("audit_events")
