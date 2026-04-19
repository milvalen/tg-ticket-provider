from __future__ import annotations

from typing import Any, Protocol

from aiogram import Bot

from core.telegram.markup_util import markup_from_json


class ITicketMessageSync(Protocol):
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


class AiogramTicketMessageSync(ITicketMessageSync):
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def publish_to_department_thread(
        self,
        *,
        chat_id: int,
        thread_id: int,
        text_html: str,
        media_file_ids: list[str],
        reply_markup_json: str | None,
    ) -> tuple[int, list[int]]:
        msg = await self._bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=text_html,
            parse_mode="HTML",
            reply_markup=markup_from_json(reply_markup_json),
        )
        main_id = msg.message_id
        extra_ids: list[int] = []
        for fid in media_file_ids:
            m = await self._bot.send_photo(
                chat_id=chat_id,
                message_thread_id=thread_id,
                photo=fid,
            )
            extra_ids.append(m.message_id)
        return main_id, extra_ids

    async def edit_ticket_message(
        self,
        *,
        chat_id: int,
        message_id: int,
        thread_id: int | None,
        text_html: str,
        reply_markup_json: str | None,
    ) -> None:
        kwargs: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text_html,
            "parse_mode": "HTML",
            "reply_markup": markup_from_json(reply_markup_json),
        }
        if thread_id is not None:
            kwargs["message_thread_id"] = thread_id
        await self._bot.edit_message_text(**kwargs)

    async def send_dm_ticket(
        self,
        *,
        user_id: int,
        text_html: str,
        media_file_ids: list[str],
        reply_markup_json: str | None,
    ) -> tuple[int, list[int]]:
        msg = await self._bot.send_message(
            chat_id=user_id,
            text=text_html,
            parse_mode="HTML",
            reply_markup=markup_from_json(reply_markup_json),
        )
        main_id = msg.message_id
        extra_ids: list[int] = []
        for fid in media_file_ids:
            m = await self._bot.send_photo(chat_id=user_id, photo=fid)
            extra_ids.append(m.message_id)
        return main_id, extra_ids
