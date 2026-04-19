from aiogram import Dispatcher

from app.use_cases.ticket_workflow import TicketWorkflow
from core.app.config import Settings

from . import admin_ticket, callbacks, employee_photo


def register_handlers(dp: Dispatcher, settings: Settings, workflow: TicketWorkflow) -> None:
    admin_ticket.register(dp, settings, workflow)
    callbacks.register(dp, settings, workflow)
    employee_photo.register(dp, settings, workflow)
