"""Inline keyboard payloads serialized as JSON for the Telegram Bot API."""

from __future__ import annotations

import json


def empty_kb() -> str | None:
    return json.dumps({"inline_keyboard": []})


def group_accept_kb(ticket_id: int) -> str:
    return json.dumps(
        {
            "inline_keyboard": [
                [{"text": "Accept", "callback_data": f"g:{ticket_id}"}],
            ]
        }
    )


def dm_take_or_return_kb(ticket_id: int) -> str:
    return json.dumps(
        {
            "inline_keyboard": [
                [
                    {"text": "Start work", "callback_data": f"w:{ticket_id}"},
                    {"text": "Return", "callback_data": f"r:{ticket_id}"},
                ],
            ]
        }
    )


def dm_work_kb(ticket_id: int) -> str:
    return json.dumps(
        {
            "inline_keyboard": [
                [{"text": "Done", "callback_data": f"d:{ticket_id}"}],
            ]
        }
    )


def pick_ticket_photo_kb(tickets: list[tuple[int, str]]) -> str:
    """Build picker rows: each item is (ticket_id, short label for the button)."""
    rows = []
    for tid, label in tickets:
        text = (label[:28] + "…") if len(label) > 30 else label
        rows.append([{"text": text, "callback_data": f"p:{tid}"}])
    return json.dumps({"inline_keyboard": rows})
