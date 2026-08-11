from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common import Ticket
from app.schemas.ticket import TicketCreateRequest


class TicketService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _next_ticket_number(self, request_type: str) -> str:
        prefix = "INC" if request_type == "incident_ticket" else "REQ"
        result = await self.db.execute(
            text(
                """
                INSERT INTO ticket_number_counters (prefix, next_number)
                VALUES (:prefix, 2)
                ON CONFLICT (prefix)
                DO UPDATE SET next_number = ticket_number_counters.next_number + 1
                RETURNING next_number - 1 AS allocated_number
                """
            ),
            {"prefix": prefix},
        )
        number = int(result.scalar_one())
        return f"{prefix}-{number:06d}"

    async def create_ticket(self, payload: TicketCreateRequest, submitted_by: str | None = None) -> Ticket:
        ticket_number = await self._next_ticket_number(payload.request_type)
        ticket = Ticket(
            ticket_number=ticket_number,
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

    async def get_ticket(self, ticket_id: str | UUID) -> Ticket | None:
        try:
            return await self.db.get(Ticket, UUID(str(ticket_id)))
        except ValueError:
            stmt = select(Ticket).where(Ticket.ticket_number == str(ticket_id).upper())
            return (await self.db.scalars(stmt)).first()

    async def search_tickets(self, query: str, limit: int = 10) -> list[Ticket]:
        stmt = select(Ticket).where(Ticket.description.ilike(f"%{query}%")).limit(limit)
        rows = (await self.db.scalars(stmt)).all()
        return list(rows)
