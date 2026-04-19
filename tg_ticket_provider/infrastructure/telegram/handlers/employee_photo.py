from aiogram import Dispatcher, F
from aiogram.enums import ChatType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from tg_ticket_provider.application.keyboards import pick_ticket_photo_kb
from tg_ticket_provider.application.ticket_workflow import TicketWorkflow
from tg_ticket_provider.config.settings import Settings
from tg_ticket_provider.infrastructure.db.db import AsyncSessionFactory
from tg_ticket_provider.infrastructure.persistence.repository import TicketRepository
from tg_ticket_provider.infrastructure.telegram.markup_util import markup_from_json
from tg_ticket_provider.infrastructure.telegram.states import AdminTicketFSM, EmployeePhotoFSM


def register(dp: Dispatcher, _settings: Settings, workflow: TicketWorkflow) -> None:
    repo = TicketRepository()

    @dp.message(
        F.photo,
        F.chat.type == ChatType.PRIVATE,
        ~StateFilter(AdminTicketFSM.photos),
    )
    async def on_employee_photo(message: Message, state: FSMContext) -> None:
        assert message.photo
        uid = message.from_user.id
        file_id = message.photo[-1].file_id

        async with AsyncSessionFactory() as session:
            tickets = await repo.list_in_progress_for_user(session, uid)
        if not tickets:
            await message.answer("You have no in-progress tickets to attach a photo to.")
            return
        if len(tickets) == 1:
            tid = tickets[0].id
            async with AsyncSessionFactory() as session:
                try:
                    await workflow.attach_photo(session, tid, uid, file_id)
                    await session.commit()
                except ValueError:
                    await session.rollback()
                    await message.answer("Could not attach the file.")
                    return
            await message.answer("Photo attached to the ticket.")
            return

        await state.set_state(EmployeePhotoFSM.picking_ticket)
        await state.update_data(pending_photo_file_id=file_id)
        pairs = [(t.id, t.title) for t in tickets]
        mk = markup_from_json(pick_ticket_photo_kb(pairs))
        assert mk is not None
        await message.answer("Which ticket is this photo for?", reply_markup=mk)

    @dp.callback_query(
        EmployeePhotoFSM.picking_ticket,
        F.data.regexp(r"^p:\d+$"),
    )
    async def on_pick_ticket_photo(query: CallbackQuery, state: FSMContext) -> None:
        if not query.message or query.message.chat.type != ChatType.PRIVATE:
            await query.answer()
            return
        assert query.data
        ticket_id = int(query.data.split(":")[1])
        uid = query.from_user.id
        data = await state.get_data()
        file_id = data.get("pending_photo_file_id")
        if not file_id:
            await query.answer("Session expired. Send the photo again.", show_alert=True)
            await state.clear()
            return
        async with AsyncSessionFactory() as session:
            try:
                await workflow.attach_photo(session, ticket_id, uid, file_id)
                await session.commit()
            except ValueError:
                await session.rollback()
                await query.answer("Could not attach.", show_alert=True)
                return
        await query.message.edit_reply_markup(reply_markup=None)
        await query.message.answer("Photo attached to the selected ticket.")
        await query.answer()
        await state.clear()
