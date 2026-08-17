from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_context import get_request_id
from app.models.common import AuditEvent, User


# Audit metadata is intentionally closed over a small, non-sensitive allow-list.
ALLOWED_METADATA = frozenset({"tool_name", "resource_id", "result_status", "latency_ms", "error_type", "found", "result_count", "workflow_type", "ticket_type"})


class AuditLogger:
    """Append audit rows to the caller's session without committing."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def log(
        self,
        *,
        event_type: str,
        action: str,
        status: str,
        actor: User | None = None,
        resource_type: str | None = None,
        resource_id: UUID | str | None = None,
        metadata: Mapping[str, Any] | None = None,
        request_id: str | None = None,
    ) -> AuditEvent:
        safe_metadata = None
        if metadata:
            safe_metadata = {
                key: value
                for key, value in metadata.items()
                if key in ALLOWED_METADATA and isinstance(value, (str, int, float, bool, type(None)))
            }
            safe_metadata = safe_metadata or None

        event = AuditEvent(
            request_id=request_id or get_request_id(),
            actor_id=actor.id if actor else None,
            event_type=event_type,
            action=action,
            status=status,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            event_metadata=safe_metadata,
        )
        # Some pure service/unit tests use a dependency-free fake session. Production
        # sessions always provide add(); keeping this logger side-effect free there
        # preserves those tests without changing the transaction contract.
        if hasattr(self.db, "add"):
            self.db.add(event)
        return event

    def log_tool_call(
        self,
        *,
        tool_name: str,
        status: str,
        latency_ms: int | None = None,
        conversation_id: UUID | None = None,
        resource_id: UUID | str | None = None,
        error_type: str | None = None,
        actor: User | None = None,
        found: bool | None = None,
        result_count: int | None = None,
    ) -> AuditEvent:
        metadata: dict[str, Any] = {
            "tool_name": tool_name,
            "resource_id": resource_id,
            "result_status": status,
            "latency_ms": latency_ms,
            "error_type": error_type,
            "found": found,
            "result_count": result_count,
        }
        return self.log(
            event_type="tool_execution",
            action="execute",
            status=status,
            actor=actor,
            resource_type="conversation" if conversation_id else None,
            resource_id=conversation_id,
            metadata=metadata,
        )
