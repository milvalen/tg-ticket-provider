from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, Column, JSON
from sqlmodel import Field

from core.db.utils import AbstractModel


class Tickets(AbstractModel, table=True):
    __tablename__ = "tickets"

    priority: str
    status: str
    title: str
    body: str
    department_thread_id: int
    group_chat_id: int = Field(sa_column=Column(BigInteger()))
    group_message_id: int | None = None
    dm_message_id: int | None = None
    assignee_user_id: int | None = Field(default=None, sa_column=Column(BigInteger()))
    admin_user_id: int = Field(sa_column=Column(BigInteger()))
    media_file_ids: list[Any] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )


class TicketAttachments(AbstractModel, table=True):
    __tablename__ = "ticket_attachments"

    ticket_id: UUID = Field(foreign_key="tickets.id")
    file_id: str
    added_by_user_id: int = Field(sa_column=Column(BigInteger()))
