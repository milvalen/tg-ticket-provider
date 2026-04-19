from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.tickets.repositories.db import TicketRepository
from app.adapters.telegram.handlers import register_handlers
from app.adapters.telegram.message_gateway import AiogramMessageSync
from app.use_cases.ticket_workflow import TicketWorkflow
from core.app.config import get_settings
from core.kpi.factory import build_kpi_sink


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    bot = Bot(
        settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    repo = TicketRepository()
    messages = AiogramMessageSync(bot)
    kpi = build_kpi_sink(settings)
    workflow = TicketWorkflow(
        repo,
        messages,
        kpi,
        staff_group_chat_id=settings.STAFF_GROUP_CHAT_ID,
    )

    register_handlers(dp, settings, workflow)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
