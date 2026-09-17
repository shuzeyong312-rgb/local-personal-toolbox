from PySide6.QtCore import QThread, Signal

from services.competitor_monitor_auto import windows_toast
from services.competitor_monitor_batch import MAX_PARALLEL_COLLECTIONS, collect_batch
from services.competitor_monitor_window import (
    BackgroundChromeEnvironment as ChromeEnvironment,
    PlaywrightCollector,
    park_monitor_chrome,
    restore_monitor_chrome,
)


class CollectionWorker(QThread):
    current = Signal(int, int, int, str)
    item_completed = Signal(int, object)
    state = Signal(str)
    environment_failed = Signal(str, str)
    verification_required = Signal(str)
    verification_stopped = Signal(str, str, int, int, int)
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
        collector = PlaywrightCollector(self.cdp_url)
        pending = list(self.competitors)
        verification_count = 0
        post_verification_successes = 0

        while pending and not self.cancelled:
            serial_recovery = verification_count and post_verification_successes < 2
            parallel = 1 if serial_recovery else min(MAX_PARALLEL_COLLECTIONS, len(pending))
            self.state.emit(
                "人工验证后串行恢复采集" if serial_recovery
                else f"正在后台并行采集（最多 {parallel} 个商品同时进行）"
            )
            batch = collect_batch(
                pending,
                collector,
                max_workers=parallel,
                cancelled=lambda: self.cancelled,
                isolate_errors=True,
            )
            verification_item = None
            try:
                for item, result in batch:
                    if result.status == "needs_verification":
                        verification_item = item
                        break
                    if result.environment_error:
                        self.environment_failed.emit(result.error, result.technical_error)
                        return
                    counts[result.status] += 1
                    pending = [candidate for candidate in pending if candidate["id"] != item["id"]]
                    self.item_completed.emit(item["id"], result)
                    if serial_recovery and result.status == "success":
                        post_verification_successes += 1
                        if post_verification_successes >= 2:
                            break
            finally:
                if verification_item is None:
                    batch.close()

            if verification_item is None:
                continue

            verification_count += 1
            restore_monitor_chrome(environment.PROFILE)
            if verification_count >= 2:
                message = "1688再次需要人工验证，本轮采集已暂停，请稍后再试。"
                windows_toast("1688竞品监控已暂停", message)
                collector.abandon_verification()
                batch.close()
                self.verification_stopped.emit(
                    message, "verification_repeated", counts["success"], counts["partial"], counts["failed"]
                )
                return

            message = "1688需要人工验证，请在专用浏览器中完成验证。验证通过后将自动继续采集。"
            self.state.emit("等待人工完成1688验证")
            windows_toast("1688需要人工验证", message)
            self.verification_required.emit(message)
            verified = collector.wait_for_verification(timeout=300, interval=1.5)
            batch.close()
            if not verified:
                message = "人工验证等待超时，本轮采集已暂停"
                windows_toast("1688竞品监控已暂停", message)
                collector.abandon_verification()
                self.verification_stopped.emit(
                    message, "verification_timeout", counts["success"], counts["partial"], counts["failed"]
                )
                return

            park_monitor_chrome(environment.PROFILE)
            target = collector.verification_target_url()
            if target:
                pending.sort(key=lambda item: item["url"] != target)
            post_verification_successes = 0
            self.state.emit("验证通过，正在恢复采集")

        self.completed.emit(self.cancelled, counts["success"], counts["partial"], counts["failed"])
