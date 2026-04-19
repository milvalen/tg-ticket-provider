from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class KpiEventType(StrEnum):
    CREATED = "created"
    PUBLISHED = "published"
    ACCEPTED_IN_GROUP = "accepted_in_group"
    RETURNED = "returned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ATTACHMENT_ADDED = "attachment_added"


@dataclass(frozen=True)
class KpiEvent:
    type: KpiEventType
    ticket_id: UUID
    at: datetime
    user_id: int | None
    department_thread_id: int | None
    priority: str | None
    extra: dict | None = None

    @staticmethod
    def now(
        type: KpiEventType,
        ticket_id: UUID,
        *,
        user_id: int | None = None,
        department_thread_id: int | None = None,
        priority: str | None = None,
        extra: dict | None = None,
    ) -> KpiEvent:
        return KpiEvent(
            type=type,
            ticket_id=ticket_id,
            at=datetime.now(timezone.utc),
            user_id=user_id,
            department_thread_id=department_thread_id,
            priority=priority,
            extra=extra,
        )


class IKpiSink(Protocol):
    async def emit(self, event: KpiEvent) -> None: ...
