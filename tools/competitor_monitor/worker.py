from PySide6.QtCore import QThread, Signal

from services.competitor_monitor_batch import MAX_PARALLEL_COLLECTIONS, collect_batch
from services.competitor_monitor_collection import BackgroundChromeEnvironment as ChromeEnvironment, PlaywrightCollector


class CollectionWorker(QThread):
    current = Signal(int, int, int, str)
    item_completed = Signal(int, object)
    state = Signal(str)
    environment_failed = Signal(str, str)
    completed = Signal(bool, int, int, int)

    def __init__(self, competitors: list[dict], cdp_url: str) -> None:
        super().__init__()
        self.competitors = competitors
        self.cdp_url = cdp_url
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def run(self) -> None:
        self.state.emit("正在准备环境")
        environment = ChromeEnvironment(self.cdp_url)
        if not environment.is_ready():
            self.state.emit("正在后台启动浏览器")
        ready = environment.ensure()
        if not ready.ready:
            self.environment_failed.emit(ready.error, ready.technical_error)
            return

        total = len(self.competitors)
        counts = {"success": 0, "partial": 0, "failed": 0}
        parallel = min(MAX_PARALLEL_COLLECTIONS, total)
        self.state.emit(f"正在并行采集（最多 {parallel} 个商品同时进行）")
        collector = PlaywrightCollector(self.cdp_url)

        for item, result in collect_batch(
            self.competitors,
            collector,
            max_workers=parallel,
            cancelled=lambda: self.cancelled,
            isolate_errors=True,
        ):
            if result.environment_error:
                self.environment_failed.emit(result.error, result.technical_error)
                return

            counts[result.status] += 1
            self.item_completed.emit(item["id"], result)

        self.completed.emit(self.cancelled, counts["success"], counts["partial"], counts["failed"])
