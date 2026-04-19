from aiogram import Dispatcher, F
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery

from app.use_cases.callback_payload import parse_ticket_uuid
from app.use_cases.ticket_workflow import TicketWorkflow
from core.app.config import Settings
from core.db.db import AsyncSessionFactory

_CALLBACK_ID = r"[0-9a-fA-F]{32}"


def register(dp: Dispatcher, settings: Settings, workflow: TicketWorkflow) -> None:
    @dp.callback_query(F.data.regexp(rf"^g:{_CALLBACK_ID}$"))
    async def on_group_accept(query: CallbackQuery) -> None:
        if not query.message or query.message.chat.id != settings.STAFF_GROUP_CHAT_ID:
            await query.answer()
            return
        assert query.data
        ticket_id = parse_ticket_uuid(query.data)
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

    @dp.callback_query(F.data.regexp(rf"^w:{_CALLBACK_ID}$"))
    async def on_dm_take_work(query: CallbackQuery) -> None:
        if not query.message or query.message.chat.type != ChatType.PRIVATE:
            await query.answer()
            return
        assert query.data
        ticket_id = parse_ticket_uuid(query.data)
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

    @dp.callback_query(F.data.regexp(rf"^r:{_CALLBACK_ID}$"))
    async def on_dm_return(query: CallbackQuery) -> None:
        if not query.message or query.message.chat.type != ChatType.PRIVATE:
            await query.answer()
            return
        assert query.data
        ticket_id = parse_ticket_uuid(query.data)
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

    @dp.callback_query(F.data.regexp(rf"^d:{_CALLBACK_ID}$"))
    async def on_dm_done(query: CallbackQuery) -> None:
        if not query.message or query.message.chat.type != ChatType.PRIVATE:
            await query.answer()
            return
        assert query.data
        ticket_id = parse_ticket_uuid(query.data)
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
