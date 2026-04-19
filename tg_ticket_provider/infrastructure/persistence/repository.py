from __future__ import annotations

from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from tg_ticket_provider.domain.entities import Priority, Ticket, TicketStatus, ticket_from_row
from tg_ticket_provider.infrastructure.persistence.models import TicketAttachmentRow, TicketRow

_UNSET: Any = object()


class TicketRepository:
    async def try_assign_if_open(
        self,
        session: AsyncSession,
        ticket_id: int,
        user_id: int,
        *,
        group_chat_id: int,
    ) -> Ticket | None:
        row = await session.get(TicketRow, ticket_id)
        if (
            row is None
            or row.status != TicketStatus.OPEN.value
            or row.group_chat_id != group_chat_id
        ):
            return None
        row.status = TicketStatus.ASSIGNED.value
        row.assignee_user_id = user_id
        session.add(row)
        await session.flush()
        await session.refresh(row)
        return ticket_from_row(row)

    async def create_draft(
        self,
        session: AsyncSession,
        *,
        priority: Priority,
        title: str,
        body: str,
        department_thread_id: int,
        group_chat_id: int,
        admin_user_id: int,
        media_file_ids: list[str],
    ) -> Ticket:
        row = TicketRow(
            priority=priority.value,
            status=TicketStatus.OPEN.value,
            title=title,
            body=body,
            department_thread_id=department_thread_id,
            group_chat_id=group_chat_id,
            admin_user_id=admin_user_id,
            media_file_ids=list(media_file_ids),
        )
        session.add(row)
        await session.flush()
        await session.refresh(row)
        return ticket_from_row(row)

    async def get_by_id(self, session: AsyncSession, ticket_id: int) -> Ticket | None:
        row = await session.get(TicketRow, ticket_id)
        if row is None:
            return None
        return ticket_from_row(row)

    async def save_message_ids(
        self,
        session: AsyncSession,
        ticket_id: int,
        *,
        group_message_id: int | None = None,
        dm_message_id: int | None = None,
    ) -> None:
        row = await session.get(TicketRow, ticket_id)
        if row is None:
            return
        if group_message_id is not None:
            row.group_message_id = group_message_id
        if dm_message_id is not None:
            row.dm_message_id = dm_message_id
        session.add(row)
        await session.flush()

    async def set_status(
        self,
        session: AsyncSession,
        ticket_id: int,
        status: TicketStatus,
        *,
        assignee_user_id: int | None | Any = _UNSET,
        clear_dm_message: bool = False,
    ) -> None:
        row = await session.get(TicketRow, ticket_id)
        if row is None:
            return
        row.status = status.value
        if assignee_user_id is not _UNSET:
            row.assignee_user_id = assignee_user_id
        if clear_dm_message:
            row.dm_message_id = None
        session.add(row)
        await session.flush()

    async def list_in_progress_for_user(
        self, session: AsyncSession, user_id: int
    ) -> list[Ticket]:
        q = (
            select(TicketRow)
            .where(TicketRow.assignee_user_id == user_id)
            .where(TicketRow.status == TicketStatus.IN_PROGRESS.value)
        )
        res = await session.exec(q)
        return [ticket_from_row(r) for r in res.all()]

    async def add_attachment(
        self, session: AsyncSession, ticket_id: int, file_id: str, user_id: int
    ) -> None:
        row = TicketAttachmentRow(ticket_id=ticket_id, file_id=file_id, added_by_user_id=user_id)
        session.add(row)
        await session.flush()
