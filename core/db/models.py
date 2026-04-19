"""Register all SQLModel table classes for Alembic metadata (see main-backend core/db/models)."""

from app.tickets.models.tickets import TicketAttachments, Tickets

__all__ = [
    "TicketAttachments",
    "Tickets",
]
