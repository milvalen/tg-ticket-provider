from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.adapters.telegram.filters import AdminFilter
from app.adapters.telegram.states import AdminTicketFSM
from app.domain.entities import Priority
from app.use_cases.ticket_workflow import TicketWorkflow
from core.app.config import Settings
from core.db.db import AsyncSessionFactory


def register(dp: Dispatcher, settings: Settings, workflow: TicketWorkflow) -> None:
    admins = settings.parsed_admin_ids()
    af = AdminFilter(admins)

    @dp.message(Command("ticket"), af)
    async def cmd_ticket(message: Message, state: FSMContext) -> None:
        await state.clear()
        kb = InlineKeyboardBuilder()
        kb.button(text="Urgent ❗", callback_data="adm:pri:u")
        kb.button(text="Normal 📌", callback_data="adm:pri:n")
        kb.adjust(2)
        await message.answer("Choose ticket priority:", reply_markup=kb.as_markup())
        await state.set_state(AdminTicketFSM.priority)

    @dp.callback_query(AdminTicketFSM.priority, F.data.startswith("adm:pri:"), af)
    async def cb_priority(query: CallbackQuery, state: FSMContext) -> None:
        assert query.data
        urgent = query.data.endswith(":u")
        await state.update_data(priority=Priority.URGENT.value if urgent else Priority.NORMAL.value)
        await query.message.edit_text("Enter a short ticket title (one line):")
        await state.set_state(AdminTicketFSM.title)
        await query.answer()

    @dp.message(AdminTicketFSM.title, af)
    async def on_title(message: Message, state: FSMContext) -> None:
        if not message.text or not message.text.strip():
            await message.answer("Title must not be empty.")
            return
        await state.update_data(title=message.text.strip()[:200])
        await message.answer("Enter the full ticket description (multiple lines allowed).")
        await state.set_state(AdminTicketFSM.body)

    @dp.message(AdminTicketFSM.body, af)
    async def on_body(message: Message, state: FSMContext) -> None:
        if not message.text or not message.text.strip():
            await message.answer("Ticket description cannot be empty.")
            return
        await state.update_data(body=message.text.strip(), photo_ids=[])
        await message.answer("Send photos one at a time, or send /next to choose a department.")
        await state.set_state(AdminTicketFSM.photos)

    @dp.message(AdminTicketFSM.photos, af, Command("next"))
    async def photos_done_cmd(message: Message, state: FSMContext) -> None:
        await _ask_department(message, state, settings)

    @dp.message(AdminTicketFSM.photos, af, F.photo)
    async def on_admin_photo(message: Message, state: FSMContext) -> None:
        assert message.photo
        fid = message.photo[-1].file_id
        data = await state.get_data()
        ids: list[str] = list(data.get("photo_ids") or [])
        ids.append(fid)
        await state.update_data(photo_ids=ids)
        await message.answer("Photo saved. Send more or /next.")

    @dp.message(AdminTicketFSM.photos, af)
    async def photos_fallback(message: Message) -> None:
        await message.answer("Send a photo or the /next command.")

    async def _ask_department(message: Message, state: FSMContext, s: Settings) -> None:
        depts = s.departments()
        if not depts:
            await message.answer("No departments configured. Set DEPARTMENTS_FILE or DEPARTMENTS_JSON.")
            await state.clear()
            return
        kb = InlineKeyboardBuilder()
        for i, d in enumerate(depts):
            kb.button(text=d.name, callback_data=f"adm:d:{i}")
        kb.adjust(1)
        await message.answer("Choose department (forum topic):", reply_markup=kb.as_markup())
        await state.set_state(AdminTicketFSM.department)

    @dp.callback_query(AdminTicketFSM.department, F.data.startswith("adm:d:"), af)
    async def cb_department(query: CallbackQuery, state: FSMContext) -> None:
        assert query.data and query.message
        idx = int(query.data.split(":")[-1])
        depts = settings.departments()
        if idx < 0 or idx >= len(depts):
            await query.answer("Invalid department.", show_alert=True)
            return
        data = await state.get_data()
        priority = Priority(data["priority"])
        title = data["title"]
        body = data["body"]
        photo_ids: list[str] = list(data.get("photo_ids") or [])

        async with AsyncSessionFactory() as session:
            try:
                await workflow.publish_new_ticket(
                    session,
                    priority=priority,
                    title=title,
                    body=body,
                    department_thread_id=depts[idx].thread_id,
                    admin_user_id=query.from_user.id,
                    media_file_ids=photo_ids,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                await query.message.edit_text("Failed to publish ticket.")
                await query.answer()
                await state.clear()
                return

        await query.message.edit_text("Ticket published.")
        await query.answer()
        await state.clear()
