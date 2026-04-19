"""Inline keyboard payloads serialized as JSON for the Telegram Bot API."""

from __future__ import annotations

import json
from uuid import UUID

from app.tickets.use_cases.callback_payload import ticket_token


def empty_kb() -> str | None:
    return json.dumps({"inline_keyboard": []})


def group_accept_kb(ticket_id: UUID) -> str:
    t = ticket_token(ticket_id)
    return json.dumps(
        {
            "inline_keyboard": [
                [{"text": "Accept", "callback_data": f"g:{t}"}],
            ]
        }
    )


def dm_take_or_return_kb(ticket_id: UUID) -> str:
    t = ticket_token(ticket_id)
    return json.dumps(
        {
            "inline_keyboard": [
                [
                    {"text": "Start work", "callback_data": f"w:{t}"},
                    {"text": "Return", "callback_data": f"r:{t}"},
                ],
            ]
        }
    )


def dm_work_kb(ticket_id: UUID) -> str:
    t = ticket_token(ticket_id)
    return json.dumps(
        {
            "inline_keyboard": [
                [{"text": "Done", "callback_data": f"d:{t}"}],
            ]
        }
    )


def pick_ticket_media_kb(tickets: list[tuple[UUID, str]]) -> str:
    """Build picker rows when several in-progress tickets: (ticket_id, label)."""
    rows = []
    for tid, label in tickets:
        text = (label[:28] + "…") if len(label) > 30 else label
        rows.append([{"text": text, "callback_data": f"p:{ticket_token(tid)}"}])
    return json.dumps({"inline_keyboard": rows})
