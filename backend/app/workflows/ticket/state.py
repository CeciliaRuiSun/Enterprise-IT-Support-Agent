from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TicketWorkflowState:
    ticket_type: str
    collected_fields: dict[str, str] = field(default_factory=dict)
    asked_fields: list[str] = field(default_factory=list)
    confirmation_pending: bool = False
    summary: str | None = None

