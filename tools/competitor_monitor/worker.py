from PySide6.QtCore import QThread, Signal

from services.competitor_monitor import ChromeEnvironment, PlaywrightCollector


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
            self.state.emit("正在启动浏览器")
        ready = environment.ensure()
        if not ready.ready:
            self.environment_failed.emit(ready.error, ready.technical_error)
            return
        collector = PlaywrightCollector(self.cdp_url)
        total = len(self.competitors)
        counts = {"success": 0, "partial": 0, "failed": 0}
        self.state.emit("正在采集")
        for index, item in enumerate(self.competitors, 1):
            if self.cancelled:
                break
            self.current.emit(index, total, item["id"], item.get("alias") or item.get("title") or item["offer_id"])
            result = collector.collect(item["url"])
            if result.environment_error:
                self.environment_failed.emit(result.error, result.technical_error)
                return
            counts[result.status] += 1
            self.item_completed.emit(item["id"], result)
        self.completed.emit(self.cancelled, counts["success"], counts["partial"], counts["failed"])
