from aiogram import Dispatcher, F
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery

from tg_ticket_provider.application.ticket_workflow import TicketWorkflow
from tg_ticket_provider.config.settings import Settings
from tg_ticket_provider.infrastructure.db.db import AsyncSessionFactory


def register(dp: Dispatcher, settings: Settings, workflow: TicketWorkflow) -> None:
    @dp.callback_query(F.data.regexp(r"^g:\d+$"))
    async def on_group_accept(query: CallbackQuery) -> None:
        if not query.message or query.message.chat.id != settings.STAFF_GROUP_CHAT_ID:
            await query.answer()
            return
        assert query.data
        ticket_id = int(query.data.split(":")[1])
        uid = query.from_user.id
        async with AsyncSessionFactory() as session:
            try:
                await workflow.accept_in_group(session, ticket_id, uid)
                await session.commit()
            except ValueError as e:
                await session.rollback()
                if str(e) == "already_taken":
                    await query.answer("This ticket was already taken.", show_alert=True)
                else:
                    await query.answer("Could not accept the ticket.", show_alert=True)
                return
        await query.answer("Open the bot chat (DM).")

    @dp.callback_query(F.data.regexp(r"^w:\d+$"))
    async def on_dm_take_work(query: CallbackQuery) -> None:
        if not query.message or query.message.chat.type != ChatType.PRIVATE:
            await query.answer()
            return
        assert query.data
        ticket_id = int(query.data.split(":")[1])
        uid = query.from_user.id
        async with AsyncSessionFactory() as session:
            try:
                await workflow.mark_in_progress(session, ticket_id, uid)
                await session.commit()
            except ValueError:
                await session.rollback()
                await query.answer("Action not allowed.", show_alert=True)
                return
        await query.answer("In progress.")

    @dp.callback_query(F.data.regexp(r"^r:\d+$"))
    async def on_dm_return(query: CallbackQuery) -> None:
        if not query.message or query.message.chat.type != ChatType.PRIVATE:
            await query.answer()
            return
        assert query.data
        ticket_id = int(query.data.split(":")[1])
        uid = query.from_user.id
        async with AsyncSessionFactory() as session:
            try:
                await workflow.return_ticket(session, ticket_id, uid)
                await session.commit()
            except ValueError:
                await session.rollback()
                await query.answer("Cannot return this ticket.", show_alert=True)
                return
        await query.answer("Ticket returned to the department.")

    @dp.callback_query(F.data.regexp(r"^d:\d+$"))
    async def on_dm_done(query: CallbackQuery) -> None:
        if not query.message or query.message.chat.type != ChatType.PRIVATE:
            await query.answer()
            return
        assert query.data
        ticket_id = int(query.data.split(":")[1])
        uid = query.from_user.id
        async with AsyncSessionFactory() as session:
            try:
                await workflow.mark_done(session, ticket_id, uid)
                await session.commit()
            except ValueError:
                await session.rollback()
                await query.answer("Cannot complete this ticket.", show_alert=True)
                return
        await query.answer("Done.")
