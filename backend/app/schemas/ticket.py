from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    request_type: str = Field(min_length=1)
    request_for: str | None = None
    business_justification: str | None = None
    description: str | None = None
    priority: str = "medium"
    assigned_to: str | None = None


class TicketResponse(BaseModel):
    ticket_id: UUID
    request_type: str
    status: str
    priority: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

