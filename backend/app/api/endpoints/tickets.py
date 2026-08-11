from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.common import Ticket, User
from app.schemas.ticket import TicketCreateRequest, TicketResponse
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: TicketCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TicketResponse:
    service = TicketService(db)
    ticket = await service.create_ticket(request, submitted_by=user.email)
    await db.commit()
    return TicketResponse(
        ticket_id=ticket.id,
        ticket_number=ticket.ticket_number,
        request_type=ticket.request_type,
        status=ticket.status,
        priority=ticket.priority,
        description=ticket.description,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    ticket = await TicketService(db).get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return TicketResponse(
        ticket_id=ticket.id,
        ticket_number=ticket.ticket_number,
        request_type=ticket.request_type,
        status=ticket.status,
        priority=ticket.priority,
        description=ticket.description,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )
