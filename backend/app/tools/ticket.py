from __future__ import annotations

from app.models.common import Ticket
from app.schemas.ticket import TicketCreateRequest


class CreateTicketTool:
    name = "create_ticket"

    def __init__(self, db) -> None:
        self.db = db

    async def run(self, payload: TicketCreateRequest, submitted_by: str | None = None) -> Ticket:
        ticket = Ticket(
            submitted_by=submitted_by,
            request_type=payload.request_type,
            request_for=payload.request_for,
            business_justification=payload.business_justification,
            description=payload.description,
            priority=payload.priority,
            assigned_to=payload.assigned_to,
            status="open",
        )
        self.db.add(ticket)
        await self.db.flush()
        return ticket

