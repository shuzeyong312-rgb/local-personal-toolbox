from PySide6.QtCore import QThread, Signal

from services.competitor_monitor import PlaywrightCollector


class CollectionWorker(QThread):
    current = Signal(int, int, int, str)
    item_completed = Signal(int, object)
    completed = Signal(bool)

    def __init__(self, competitors: list[dict], cdp_url: str) -> None:
        super().__init__()
        self.competitors = competitors
        self.cdp_url = cdp_url
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def run(self) -> None:
        collector = PlaywrightCollector(self.cdp_url)
        total = len(self.competitors)
        for index, item in enumerate(self.competitors, 1):
            if self.cancelled:
                break
            self.current.emit(index, total, item["id"], item.get("alias") or item.get("title") or item["offer_id"])
            self.item_completed.emit(item["id"], collector.collect(item["url"]))
        self.completed.emit(self.cancelled)
