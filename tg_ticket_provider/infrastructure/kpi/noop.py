import logging

from tg_ticket_provider.application.kpi_port import IKpiSink, KpiEvent

log = logging.getLogger(__name__)


class NoOpKpiSink(IKpiSink):
    async def emit(self, event: KpiEvent) -> None:
        log.debug("kpi %s ticket=%s", event.type, event.ticket_id)
