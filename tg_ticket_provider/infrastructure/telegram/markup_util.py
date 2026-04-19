from __future__ import annotations

import json
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def markup_from_json(reply_markup_json: str | None) -> InlineKeyboardMarkup | None:
    if not reply_markup_json:
        return None
    raw: dict[str, Any] = json.loads(reply_markup_json)
    rows_raw = raw.get("inline_keyboard") or []
    if not rows_raw:
        return None
    rows: list[list[InlineKeyboardButton]] = []
    for row in rows_raw:
        rows.append(
            [
                InlineKeyboardButton(text=b["text"], callback_data=b["callback_data"])
                for b in row
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)
