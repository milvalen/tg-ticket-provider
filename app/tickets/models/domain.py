from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class Priority(StrEnum):
    URGENT = "urgent"
    NORMAL = "normal"


class TicketStatus(StrEnum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class Ticket:
    id: UUID
    priority: Priority
    status: TicketStatus
    title: str
    body: str
    department_thread_id: int
    group_chat_id: int
    group_message_id: int | None
    dm_message_id: int | None
    assignee_user_id: int | None
    admin_user_id: int
    media_file_ids: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def can_accept_in_group(self) -> bool:
        return self.status == TicketStatus.OPEN and self.assignee_user_id is None

    def can_return(self, user_id: int) -> bool:
        return self.status == TicketStatus.ASSIGNED and self.assignee_user_id == user_id

    def can_start_work(self, user_id: int) -> bool:
        return self.status == TicketStatus.ASSIGNED and self.assignee_user_id == user_id

    def can_mark_done(self, user_id: int) -> bool:
        return (
            self.status == TicketStatus.IN_PROGRESS and self.assignee_user_id == user_id
        )


def transition_assign_from_group(ticket: Ticket, user_id: int) -> Ticket:
    if not ticket.can_accept_in_group():
        raise ValueError("ticket_not_open")
    ticket.status = TicketStatus.ASSIGNED
    ticket.assignee_user_id = user_id
    return ticket


def transition_return_to_group(ticket: Ticket, user_id: int) -> Ticket:
    if not ticket.can_return(user_id):
        raise ValueError("cannot_return")
    ticket.status = TicketStatus.OPEN
    ticket.assignee_user_id = None
    ticket.dm_message_id = None
    return ticket


def transition_start_work(ticket: Ticket, user_id: int) -> Ticket:
    if not ticket.can_start_work(user_id):
        raise ValueError("cannot_start_work")
    ticket.status = TicketStatus.IN_PROGRESS
    return ticket


def transition_done(ticket: Ticket, user_id: int) -> Ticket:
    if not ticket.can_mark_done(user_id):
        raise ValueError("cannot_done")
    ticket.status = TicketStatus.DONE
    return ticket


def ticket_from_row(row: Any) -> Ticket:
    """Map an ORM row or dict-like object to a domain Ticket."""
    return Ticket(
        id=row.id,
        priority=Priority(row.priority),
        status=TicketStatus(row.status),
        title=row.title,
        body=row.body,
        department_thread_id=row.department_thread_id,
        group_chat_id=row.group_chat_id,
        group_message_id=row.group_message_id,
        dm_message_id=row.dm_message_id,
        assignee_user_id=row.assignee_user_id,
        admin_user_id=row.admin_user_id,
        media_file_ids=list(row.media_file_ids or []),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
