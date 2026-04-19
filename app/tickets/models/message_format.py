from __future__ import annotations

from dataclasses import dataclass

from app.tickets.models.domain import Priority, Ticket, TicketStatus


@dataclass(frozen=True)
class TicketMessageView:
    """Rendered text for a Telegram message (group thread or DM)."""

    full_text: str


def _status_emoji(status: TicketStatus) -> str:
    if status == TicketStatus.DONE:
        return "✅"
    if status == TicketStatus.IN_PROGRESS:
        return "⏳"
    return ""


def _priority_prefix(priority: Priority) -> str:
    if priority == Priority.URGENT:
        return "❗ "
    return "📌 "


def render_ticket_caption(
    ticket: Ticket,
    *,
    for_dm: bool = False,
    assignee_hint: str | None = None,
) -> str:
    status_e = _status_emoji(ticket.status)
    pri = _priority_prefix(ticket.priority)
    header_parts = [p for p in [status_e, pri.strip()] if p]
    header = (" ".join(header_parts) + "\n\n") if header_parts else ""

    lines = [
        f"{header}<b>{_escape_html(ticket.title)}</b>",
        "",
        _escape_html(ticket.body),
    ]
    if for_dm and assignee_hint:
        lines.extend(["", f"<i>{_escape_html(assignee_hint)}</i>"])
    return "\n".join(lines).strip()


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
