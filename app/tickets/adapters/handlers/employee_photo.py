from aiogram import Dispatcher, F
from aiogram.enums import ChatType, ContentType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.tickets.adapters.telegram.states import AdminTicketFSM, EmployeePhotoFSM
from app.tickets.repositories.db import TicketRepository
from app.tickets.repositories.telegram import TicketTelegramRepository
from app.tickets.use_cases.callback_payload import parse_ticket_uuid
from app.tickets.use_cases.keyboards import pick_ticket_media_kb
from core.app.config import Settings
from core.db.db import AsyncSessionFactory
from core.telegram.markup_util import markup_from_json


def _report_file_id(message: Message) -> str | None:
    """Telegram file_id for a photo, video, video note, animation, or video document."""
    if message.photo:
        return message.photo[-1].file_id
    if message.video:
        return message.video.file_id
    if message.video_note:
        return message.video_note.file_id
    if message.animation:
        return message.animation.file_id
    doc = message.document
    if doc and doc.mime_type and doc.mime_type.startswith("video/"):
        return doc.file_id
    return None


def register(dp: Dispatcher, _settings: Settings, ticket_telegram: TicketTelegramRepository) -> None:
    repo = TicketRepository()

    @dp.message(
        F.chat.type == ChatType.PRIVATE,
        ~StateFilter(AdminTicketFSM.photos),
        F.content_type.in_(
            {
                ContentType.PHOTO,
                ContentType.VIDEO,
                ContentType.VIDEO_NOTE,
                ContentType.ANIMATION,
                ContentType.DOCUMENT,
            }
        ),
    )
    async def on_employee_report(message: Message, state: FSMContext) -> None:
        file_id = _report_file_id(message)
        if file_id is None:
            await message.answer(
                "Send a photo, video, video note, or a video file as a report for your task."
            )
            return
        uid = message.from_user.id

        async with AsyncSessionFactory() as session:
            tickets = await repo.list_in_progress_for_user(session, uid)
        if not tickets:
            await message.answer(
                "You have no in-progress tickets to attach a photo or video report to."
            )
            return
        if len(tickets) == 1:
            tid = tickets[0].id
            async with AsyncSessionFactory() as session:
                try:
                    await ticket_telegram.attach_report(session, tid, uid, file_id)
                    await session.commit()
                except ValueError:
                    await session.rollback()
                    await message.answer("Could not attach the file.")
                    return
            await message.answer("Report attached to the ticket.")
            return

        await state.set_state(EmployeePhotoFSM.picking_ticket)
        await state.update_data(pending_attachment_file_id=file_id)
        pairs = [(t.id, t.title) for t in tickets]
        mk = markup_from_json(pick_ticket_media_kb(pairs))
        assert mk is not None
        await message.answer(
            "Which ticket is this photo or video for?", reply_markup=mk
        )

    @dp.callback_query(
        EmployeePhotoFSM.picking_ticket,
        F.data.regexp(r"^p:[0-9a-fA-F]{32}$"),
    )
    async def on_pick_ticket_photo(query: CallbackQuery, state: FSMContext) -> None:
        if not query.message or query.message.chat.type != ChatType.PRIVATE:
            await query.answer()
            return
        assert query.data
        ticket_id = parse_ticket_uuid(query.data)
        uid = query.from_user.id
        data = await state.get_data()
        file_id = data.get("pending_attachment_file_id")
        if not file_id:
            await query.answer(
                "Session expired. Send the photo or video again.", show_alert=True
            )
            await state.clear()
            return
        async with AsyncSessionFactory() as session:
            try:
                await ticket_telegram.attach_report(session, ticket_id, uid, file_id)
                await session.commit()
            except ValueError:
                await session.rollback()
                await query.answer("Could not attach.", show_alert=True)
                return
        await query.message.edit_reply_markup(reply_markup=None)
        await query.message.answer("Report attached to the selected ticket.")
        await query.answer()
        await state.clear()
