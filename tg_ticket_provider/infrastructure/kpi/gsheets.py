from __future__ import annotations

import asyncio
import logging

import gspread

from tg_ticket_provider.application.kpi_port import IKpiSink, KpiEvent, KpiEventType
from tg_ticket_provider.config.settings import Settings

log = logging.getLogger(__name__)

_WORKSHEET_TITLE = "Department_KPI"
_HEADERS = [
    "timestamp_utc",
    "department_thread_id",
    "department_name",
    "event_type",
    "ticket_id",
    "priority",
    "actor_user_id",
    "dept_intake",
    "dept_queue_back",
    "dept_claimed",
    "dept_active_work",
    "dept_cleared",
    "complexity_signal",
    "net_queue_delta",
]


def _flags_for_event(event: KpiEvent) -> tuple[int, int, int, int, int, int, int]:
    """Return intake, queue_back, claimed, active_work, cleared, complexity, net_queue_delta for department load KPI."""
    t = event.type
    intake = 1 if t == KpiEventType.PUBLISHED else 0
    queue_back = 1 if t == KpiEventType.RETURNED else 0
    claimed = 1 if t == KpiEventType.ACCEPTED_IN_GROUP else 0
    active_work = 1 if t == KpiEventType.IN_PROGRESS else 0
    cleared = 1 if t == KpiEventType.DONE else 0
    complexity = 1 if t == KpiEventType.ATTACHMENT_ADDED else 0
    net_queue_delta = intake + queue_back - claimed - cleared
    return intake, queue_back, claimed, active_work, cleared, complexity, net_queue_delta


class GoogleSheetsKpiSink(IKpiSink):
    """Append KPI rows to a shared spreadsheet (test metrics for department load)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID
        self._sa_path = settings.GOOGLE_SERVICE_ACCOUNT_FILE
        self._append_lock = asyncio.Lock()

    def _department_name(self, thread_id: int | None) -> str:
        if thread_id is None:
            return ""
        for d in self._settings.departments():
            if d.thread_id == thread_id:
                return d.name
        return str(thread_id)

    def _append_sync(self, event: KpiEvent) -> None:
        gc = gspread.service_account(filename=self._sa_path)
        sh = gc.open_by_key(self._spreadsheet_id)
        try:
            ws = sh.worksheet(_WORKSHEET_TITLE)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=_WORKSHEET_TITLE, rows=2000, cols=len(_HEADERS))
            ws.append_row(_HEADERS, value_input_option="USER_ENTERED")
        intake, qback, claimed, active, cleared, complexity, net_q = _flags_for_event(event)
        row = [
            event.at.isoformat(),
            "" if event.department_thread_id is None else str(event.department_thread_id),
            self._department_name(event.department_thread_id),
            event.type.value,
            str(event.ticket_id),
            "" if event.priority is None else event.priority,
            "" if event.user_id is None else str(event.user_id),
            str(intake),
            str(qback),
            str(claimed),
            str(active),
            str(cleared),
            str(complexity),
            str(net_q),
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")

    async def emit(self, event: KpiEvent) -> None:
        async with self._append_lock:
            try:
                await asyncio.to_thread(self._append_sync, event)
            except Exception:
                log.exception(
                    "kpi_gsheets_append_failed ticket=%s type=%s",
                    event.ticket_id,
                    event.type,
                )
