from aiogram.fsm.state import State, StatesGroup


class AdminTicketFSM(StatesGroup):
    priority = State()
    title = State()
    body = State()
    photos = State()
    department = State()


class EmployeePhotoFSM(StatesGroup):
    picking_ticket = State()
