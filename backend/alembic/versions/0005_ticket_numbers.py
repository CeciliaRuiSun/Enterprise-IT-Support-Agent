"""add human-readable ticket numbers

Revision ID: 0005_ticket_numbers
Revises: 0004_close_conversations
Create Date: 2026-08-10 00:00:00.000000
"""

from collections import defaultdict

from alembic import op
import sqlalchemy as sa


revision = "0005_ticket_numbers"
down_revision = "0004_close_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("ticket_number", sa.String(length=10), nullable=True))

    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, request_type FROM tickets ORDER BY created_at, id")
    ).mappings()
    counters: defaultdict[str, int] = defaultdict(int)

    for row in rows:
        prefix = "INC" if row["request_type"] == "incident_ticket" else "REQ"
        counters[prefix] += 1
        bind.execute(
            sa.text("UPDATE tickets SET ticket_number = :ticket_number WHERE id = :ticket_id"),
            {
                "ticket_number": f"{prefix}-{counters[prefix]:06d}",
                "ticket_id": row["id"],
            },
        )

    op.alter_column("tickets", "ticket_number", nullable=False)
    op.create_unique_constraint("uq_tickets_ticket_number", "tickets", ["ticket_number"])
    op.create_table(
        "ticket_number_counters",
        sa.Column("prefix", sa.String(length=3), primary_key=True),
        sa.Column("next_number", sa.Integer(), nullable=False),
    )
    bind.execute(
        sa.text(
            "INSERT INTO ticket_number_counters (prefix, next_number) VALUES (:inc, :inc_next), (:req, :req_next)"
        ),
        {
            "inc": "INC",
            "inc_next": counters["INC"] + 1,
            "req": "REQ",
            "req_next": counters["REQ"] + 1,
        },
    )


def downgrade() -> None:
    op.drop_table("ticket_number_counters")
    op.drop_constraint("uq_tickets_ticket_number", "tickets", type_="unique")
    op.drop_column("tickets", "ticket_number")
