from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Column, DateTime, JSON, func
from sqlmodel import Field, SQLModel


class TicketRow(SQLModel, table=True):
    __tablename__ = "tickets"

    id: int | None = Field(default=None, primary_key=True)
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
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=False),
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )


class TicketAttachmentRow(SQLModel, table=True):
    __tablename__ = "ticket_attachments"

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="tickets.id")
    file_id: str
    added_by_user_id: int = Field(sa_column=Column(BigInteger()))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
    )
