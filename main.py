import sys
from pathlib import Path


def run_auto_monitor() -> int:
    from PySide6.QtCore import QSettings
    from services.competitor_monitor import MonitorStore
    from services.competitor_monitor_auto import AutoMonitor

    settings = QSettings("LocalToolbox", "competitor_monitor")
    store = MonitorStore(Path(__file__).parent / "data" / "competitor_monitor.db")
    try:
        AutoMonitor(
            store,
            scheduled_time=str(settings.value("scheduled_time", "09:00")),
            cdp_url=str(settings.value("cdp_url", "http://127.0.0.1:9222")),
            price_threshold=float(settings.value("price_threshold", 5)),
            sales_threshold=int(settings.value("sales_threshold", 20)),
            notification_enabled=settings.value("notification_enabled", True, type=bool),
        ).run()
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    if "--competitor-monitor-auto" in sys.argv:
        raise SystemExit(run_auto_monitor())
    from app.main_window import run
    raise SystemExit(run())
