"""Compact ticket id in Telegram callback_data (prefix + 32-char UUID hex)."""

from __future__ import annotations

import re
from uuid import UUID

_HEX32 = re.compile(r"^[0-9a-f]{32}$", re.IGNORECASE)


def ticket_token(ticket_id: UUID) -> str:
    return ticket_id.hex


def parse_ticket_uuid(callback_data: str) -> UUID:
    _prefix, sep, tail = callback_data.partition(":")
    if not sep or not tail:
        raise ValueError("bad_callback")
    if len(tail) == 32 and _HEX32.fullmatch(tail):
        return UUID(hex=tail)
    return UUID(tail)
