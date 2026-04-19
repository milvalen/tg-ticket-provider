import logging

from core.kpi.protocol import IKpiSink
from core.app.config import Settings
from core.kpi.noop import NoOpKpiSink

log = logging.getLogger(__name__)


def build_kpi_sink(settings: Settings) -> IKpiSink:
    sid = (settings.GOOGLE_SHEETS_SPREADSHEET_ID or "").strip()
    sa = (settings.GOOGLE_SERVICE_ACCOUNT_FILE or "").strip()
    if sid and sa:
        from core.kpi.gsheets import GoogleSheetsKpiSink

        return GoogleSheetsKpiSink(settings)
    if sid or sa:
        log.warning("Set both GOOGLE_SHEETS_SPREADSHEET_ID and GOOGLE_SERVICE_ACCOUNT_FILE for KPI export; using no-op sink.")
    return NoOpKpiSink()
