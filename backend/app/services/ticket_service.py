from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common import Ticket
from app.schemas.ticket import TicketCreateRequest


class TicketService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_ticket(self, payload: TicketCreateRequest, submitted_by: str | None = None) -> Ticket:
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

    async def get_ticket(self, ticket_id) -> Ticket | None:
        return await self.db.get(Ticket, ticket_id)

    async def search_tickets(self, query: str, limit: int = 10) -> list[Ticket]:
        stmt = select(Ticket).where(Ticket.description.ilike(f"%{query}%")).limit(limit)
        rows = (await self.db.scalars(stmt)).all()
        return list(rows)

