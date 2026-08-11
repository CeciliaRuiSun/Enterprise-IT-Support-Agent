from __future__ import annotations

from app.schemas.ticket import TicketCreateRequest
from app.models.common import Ticket
from app.services.ticket_service import TicketService


class CreateTicketTool:
    name = "create_ticket"

    def __init__(self, db) -> None:
        self.db = db

    async def run(self, payload: TicketCreateRequest, submitted_by: str | None = None) -> Ticket:
        return await TicketService(self.db).create_ticket(payload, submitted_by=submitted_by)
