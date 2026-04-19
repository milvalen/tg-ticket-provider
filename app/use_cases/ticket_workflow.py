from __future__ import annotations

from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from app.use_cases.keyboards import (
    dm_take_or_return_kb,
    dm_work_kb,
    empty_kb,
    group_accept_kb,
)
from app.use_cases.ports import IMessageSync, ITicketRepository
from core.kpi.protocol import IKpiSink, KpiEvent, KpiEventType
from app.domain.entities import (
    Priority,
    Ticket,
    TicketStatus,
    transition_done,
    transition_return_to_group,
    transition_start_work,
)
from app.domain.message_format import render_ticket_caption


class TicketWorkflow:
    def __init__(
        self,
        repo: ITicketRepository,
        messages: IMessageSync,
        kpi: IKpiSink,
        staff_group_chat_id: int,
    ) -> None:
        self._repo = repo
        self._messages = messages
        self._kpi = kpi
        self._staff_group_chat_id = staff_group_chat_id

    async def publish_new_ticket(
        self,
        session: AsyncSession,
        *,
        priority: Priority,
        title: str,
        body: str,
        department_thread_id: int,
        admin_user_id: int,
        media_file_ids: list[str],
    ) -> Ticket:
        ticket = await self._repo.create_draft(
            session,
            priority=priority,
            title=title,
            body=body,
            department_thread_id=department_thread_id,
            group_chat_id=self._staff_group_chat_id,
            admin_user_id=admin_user_id,
            media_file_ids=media_file_ids,
        )
        text = render_ticket_caption(ticket, for_dm=False)
        main_id, extras = await self._messages.publish_to_department_thread(
            chat_id=self._staff_group_chat_id,
            thread_id=department_thread_id,
            text_html=text,
            media_file_ids=media_file_ids,
            reply_markup_json=group_accept_kb(ticket.id),
        )
        await self._repo.save_message_ids(
            session, ticket.id, group_message_id=main_id
        )
        ticket.group_message_id = main_id
        await self._kpi.emit(
            KpiEvent.now(
                KpiEventType.PUBLISHED,
                ticket.id,
                user_id=admin_user_id,
                department_thread_id=department_thread_id,
                priority=priority.value,
            )
        )
        return ticket

    async def accept_in_group(
        self, session: AsyncSession, ticket_id: UUID, user_id: int
    ) -> Ticket:
        ticket = await self._repo.try_assign_if_open(
            session,
            ticket_id,
            user_id,
            group_chat_id=self._staff_group_chat_id,
        )
        if ticket is None:
            raise ValueError("already_taken")

        text_dm = render_ticket_caption(
            ticket,
            for_dm=True,
            assignee_hint="Assigned to you. Start work or return to the department thread.",
        )
        text_group = render_ticket_caption(ticket, for_dm=False)
        dm_main, _ = await self._messages.send_dm_ticket(
            user_id=user_id,
            text_html=text_dm,
            media_file_ids=ticket.media_file_ids,
            reply_markup_json=dm_take_or_return_kb(ticket.id),
        )
        await self._repo.save_message_ids(session, ticket_id, dm_message_id=dm_main)

        if ticket.group_message_id:
            await self._messages.edit_ticket_message(
                chat_id=self._staff_group_chat_id,
                message_id=ticket.group_message_id,
                thread_id=ticket.department_thread_id,
                text_html=text_group,
                reply_markup_json=empty_kb(),
            )

        await self._kpi.emit(
            KpiEvent.now(
                KpiEventType.ACCEPTED_IN_GROUP,
                ticket_id,
                user_id=user_id,
                department_thread_id=ticket.department_thread_id,
                priority=ticket.priority.value,
            )
        )
        return ticket

    async def return_ticket(
        self, session: AsyncSession, ticket_id: UUID, user_id: int
    ) -> Ticket:
        row = await self._repo.get_by_id(session, ticket_id)
        if row is None:
            raise ValueError("not_found")
        ticket = row
        dm_mid = ticket.dm_message_id
        transition_return_to_group(ticket, user_id)
        await self._repo.set_status(
            session,
            ticket_id,
            TicketStatus.OPEN,
            assignee_user_id=None,
            clear_dm_message=True,
        )

        text = render_ticket_caption(ticket, for_dm=False)
        if ticket.group_message_id:
            await self._messages.edit_ticket_message(
                chat_id=self._staff_group_chat_id,
                message_id=ticket.group_message_id,
                thread_id=ticket.department_thread_id,
                text_html=text,
                reply_markup_json=group_accept_kb(ticket.id),
            )
        if dm_mid:
            await self._messages.edit_ticket_message(
                chat_id=user_id,
                message_id=dm_mid,
                thread_id=None,
                text_html=text + "\n\n<i>Ticket returned to the department.</i>",
                reply_markup_json=empty_kb(),
            )

        await self._kpi.emit(
            KpiEvent.now(
                KpiEventType.RETURNED,
                ticket_id,
                user_id=user_id,
                department_thread_id=ticket.department_thread_id,
                priority=ticket.priority.value,
            )
        )
        return ticket

    async def mark_in_progress(
        self, session: AsyncSession, ticket_id: UUID, user_id: int
    ) -> Ticket:
        row = await self._repo.get_by_id(session, ticket_id)
        if row is None:
            raise ValueError("not_found")
        ticket = row
        transition_start_work(ticket, user_id)
        await self._repo.set_status(session, ticket_id, TicketStatus.IN_PROGRESS)

        text_g = render_ticket_caption(ticket, for_dm=False)
        text_d = render_ticket_caption(
            ticket,
            for_dm=True,
            assignee_hint="In progress. Tap Done when finished.",
        )
        if ticket.group_message_id:
            await self._messages.edit_ticket_message(
                chat_id=self._staff_group_chat_id,
                message_id=ticket.group_message_id,
                thread_id=ticket.department_thread_id,
                text_html=text_g,
                reply_markup_json=empty_kb(),
            )
        if ticket.dm_message_id:
            await self._messages.edit_ticket_message(
                chat_id=user_id,
                message_id=ticket.dm_message_id,
                thread_id=None,
                text_html=text_d,
                reply_markup_json=dm_work_kb(ticket.id),
            )

        await self._kpi.emit(
            KpiEvent.now(
                KpiEventType.IN_PROGRESS,
                ticket_id,
                user_id=user_id,
                department_thread_id=ticket.department_thread_id,
                priority=ticket.priority.value,
            )
        )
        return ticket

    async def mark_done(
        self, session: AsyncSession, ticket_id: UUID, user_id: int
    ) -> Ticket:
        row = await self._repo.get_by_id(session, ticket_id)
        if row is None:
            raise ValueError("not_found")
        ticket = row
        transition_done(ticket, user_id)
        await self._repo.set_status(session, ticket_id, TicketStatus.DONE)

        text_g = render_ticket_caption(ticket, for_dm=False)
        text_d = render_ticket_caption(
            ticket, for_dm=True, assignee_hint="Completed."
        )
        if ticket.group_message_id:
            await self._messages.edit_ticket_message(
                chat_id=self._staff_group_chat_id,
                message_id=ticket.group_message_id,
                thread_id=ticket.department_thread_id,
                text_html=text_g,
                reply_markup_json=empty_kb(),
            )
        if ticket.dm_message_id:
            await self._messages.edit_ticket_message(
                chat_id=user_id,
                message_id=ticket.dm_message_id,
                thread_id=None,
                text_html=text_d,
                reply_markup_json=empty_kb(),
            )

        await self._kpi.emit(
            KpiEvent.now(
                KpiEventType.DONE,
                ticket_id,
                user_id=user_id,
                department_thread_id=ticket.department_thread_id,
                priority=ticket.priority.value,
            )
        )
        return ticket

    async def attach_photo(
        self, session: AsyncSession, ticket_id: UUID, user_id: int, file_id: str
    ) -> None:
        t = await self._repo.get_by_id(session, ticket_id)
        if t is None or t.assignee_user_id != user_id:
            raise ValueError("forbidden")
        if t.status != TicketStatus.IN_PROGRESS:
            raise ValueError("not_in_progress")
        await self._repo.add_attachment(session, ticket_id, file_id, user_id)
        await self._kpi.emit(
            KpiEvent.now(
                KpiEventType.ATTACHMENT_ADDED,
                ticket_id,
                user_id=user_id,
                department_thread_id=t.department_thread_id,
                priority=t.priority.value,
                extra={"file_id": file_id},
            )
        )
