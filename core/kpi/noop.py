import logging

from core.kpi.protocol import IKpiSink, KpiEvent

log = logging.getLogger(__name__)


class NoOpKpiSink(IKpiSink):
    async def emit(self, event: KpiEvent) -> None:
        log.debug("kpi %s ticket=%s", event.type, event.ticket_id)
