import logging

from tg_ticket_provider.application.kpi_port import IKpiSink
from tg_ticket_provider.config.settings import Settings
from tg_ticket_provider.infrastructure.kpi.gsheets import GoogleSheetsKpiSink
from tg_ticket_provider.infrastructure.kpi.noop import NoOpKpiSink

log = logging.getLogger(__name__)


def build_kpi_sink(settings: Settings) -> IKpiSink:
    sid = (settings.GOOGLE_SHEETS_SPREADSHEET_ID or "").strip()
    sa = (settings.GOOGLE_SERVICE_ACCOUNT_FILE or "").strip()
    if sid and sa:
        return GoogleSheetsKpiSink(settings)
    if sid or sa:
        log.warning("Set both GOOGLE_SHEETS_SPREADSHEET_ID and GOOGLE_SERVICE_ACCOUNT_FILE for KPI export; using no-op sink.")
    return NoOpKpiSink()
