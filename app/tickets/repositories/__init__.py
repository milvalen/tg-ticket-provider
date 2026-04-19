from app.tickets.repositories.db import ITicketRepository, TicketRepository
from app.tickets.repositories.telegram import TicketTelegramRepository

__all__ = ["ITicketRepository", "TicketRepository", "TicketTelegramRepository"]
