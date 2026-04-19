from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from tg_ticket_provider.application.ticket_workflow import TicketWorkflow
from tg_ticket_provider.config.settings import get_settings
from tg_ticket_provider.infrastructure.kpi.noop import NoOpKpiSink
from tg_ticket_provider.infrastructure.persistence.repository import TicketRepository
from tg_ticket_provider.infrastructure.telegram.handlers import register_handlers
from tg_ticket_provider.infrastructure.telegram.message_gateway import AiogramMessageSync


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
    kpi = NoOpKpiSink()
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
