from __future__ import annotations

from typing import Protocol

from sqlmodel.ext.asyncio.session import AsyncSession

from tg_ticket_provider.domain.entities import Priority, Ticket, TicketStatus


class ITicketRepository(Protocol):
    async def try_assign_if_open(
        self,
        session: AsyncSession,
        ticket_id: int,
        user_id: int,
        *,
        group_chat_id: int,
    ) -> Ticket | None: ...

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
    ) -> Ticket: ...

    async def get_by_id(self, session: AsyncSession, ticket_id: int) -> Ticket | None: ...

    async def save_message_ids(
        self,
        session: AsyncSession,
        ticket_id: int,
        *,
        group_message_id: int | None = None,
        dm_message_id: int | None = None,
    ) -> None: ...

    async def set_status(
        self,
        session: AsyncSession,
        ticket_id: int,
        status: TicketStatus,
        *,
        assignee_user_id: int | None = None,
        clear_dm_message: bool = False,
    ) -> None: ...

    async def list_in_progress_for_user(
        self, session: AsyncSession, user_id: int
    ) -> list[Ticket]: ...

    async def add_attachment(
        self, session: AsyncSession, ticket_id: int, file_id: str, user_id: int
    ) -> None: ...


class IMessageSync(Protocol):
    """Outbound Telegram: publish and edit ticket messages."""

    async def publish_to_department_thread(
        self,
        *,
        chat_id: int,
        thread_id: int,
        text_html: str,
        media_file_ids: list[str],
        reply_markup_json: str | None,
    ) -> tuple[int, list[int]]:
        """Post to forum thread; returns (main_message_id, extra_media_message_ids)."""
        ...

    async def edit_ticket_message(
        self,
        *,
        chat_id: int,
        message_id: int,
        thread_id: int | None,
        text_html: str,
        reply_markup_json: str | None,
    ) -> None: ...

    async def send_dm_ticket(
        self,
        *,
        user_id: int,
        text_html: str,
        media_file_ids: list[str],
        reply_markup_json: str | None,
    ) -> tuple[int, list[int]]:
        """Returns (main_dm_message_id, extra_media_message_ids)."""
        ...
