from aiogram import Dispatcher

from app.tickets.repositories.telegram import TicketTelegramRepository
from core.app.config import Settings

from . import admin_ticket, callbacks, employee_photo


def register_handlers(
    dp: Dispatcher,
    settings: Settings,
    ticket_telegram: TicketTelegramRepository,
) -> None:
    admin_ticket.register(dp, settings, ticket_telegram)
    callbacks.register(dp, settings, ticket_telegram)
    employee_photo.register(dp, settings, ticket_telegram)
