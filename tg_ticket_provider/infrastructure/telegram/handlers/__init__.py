from aiogram import Dispatcher

from tg_ticket_provider.application.ticket_workflow import TicketWorkflow
from tg_ticket_provider.config.settings import Settings
from tg_ticket_provider.infrastructure.telegram.handlers import admin_ticket, callbacks, employee_photo


def register_handlers(dp: Dispatcher, settings: Settings, workflow: TicketWorkflow) -> None:
    admin_ticket.register(dp, settings, workflow)
    callbacks.register(dp, settings, workflow)
    employee_photo.register(dp, settings, workflow)
