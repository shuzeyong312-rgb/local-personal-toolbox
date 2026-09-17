import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from services.competitor_monitor import CollectionResult, MonitorStore, normalize_collection
from tests.test_competitor_monitor import complete_raw
from tools.competitor_monitor.page import CompetitorMonitorPage
from tools.competitor_monitor.worker import CollectionWorker


URLS = [
    "https://detail.1688.com/offer/976443859503.html",
    "https://detail.1688.com/offer/1045639948434.html",
]


class CompetitorMonitorAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_sqlite_survives_reopen_and_snapshots_append(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "monitor.db"
            store = MonitorStore(path)
            competitor_id, _ = store.add_competitor(URLS[0], alias="A404", note="重点观察")
            data = normalize_collection(complete_raw())
            store.save_collection(competitor_id, CollectionResult("success", data))
            store.save_collection(competitor_id, CollectionResult("success", data))
            store.close()

            reopened = MonitorStore(path)
            row = reopened.competitor(competitor_id)
            self.assertEqual(("A404", "重点观察"), (row["alias"], row["note"]))
            self.assertEqual(2, reopened.competitors()[0]["snapshot_count"])
            reopened.close()

    def test_group_changes_preserve_competitor_and_snapshots(self):
        with tempfile.TemporaryDirectory() as name:
            store = MonitorStore(Path(name) / "monitor.db")
            group_id = store.add_group("暖手宝")
            competitor_id, _ = store.add_competitor(URLS[0], group_id)
            store.save_collection(competitor_id, CollectionResult("success", normalize_collection(complete_raw())))
            store.rename_group(group_id, "小家电")
            self.assertEqual("小家电", store.competitors()[0]["group_name"])
            store.delete_group(group_id)
            self.assertIsNotNone(store.competitor(competitor_id))
            self.assertIsNotNone(store.latest_snapshot(competitor_id))
            self.assertIsNone(store.competitor(competitor_id)["group_id"])
            store.close()

    def test_batch_collection_excludes_paused_competitor(self):
        with tempfile.TemporaryDirectory() as name:
            page = CompetitorMonitorPage(Path(name) / "monitor.db")
            active_id, _ = page.store.add_competitor(URLS[0])
            paused_id, _ = page.store.add_competitor(URLS[1])
            page.store.set_enabled(paused_id, False)
            with patch.object(page, "start_collection") as start:
                page.collect_all()
            self.assertEqual([active_id], start.call_args.args[0])
            page.store.close()

    def test_one_failure_does_not_stop_batch_worker(self):
        items = [
            {"id": 1, "url": URLS[0], "offer_id": "976443859503", "alias": None, "title": None},
            {"id": 2, "url": URLS[1], "offer_id": "1045639948434", "alias": None, "title": None},
        ]
        results = []
        with patch("tools.competitor_monitor.worker.PlaywrightCollector.collect", side_effect=[
            CollectionResult("failed", error="页面打不开"),
            CollectionResult("success", normalize_collection(complete_raw())),
        ]):
            worker = CollectionWorker(items, "http://127.0.0.1:9222")
            worker.item_completed.connect(lambda competitor_id, result: results.append((competitor_id, result.status)))
            worker.run()
        self.assertEqual([(1, "failed"), (2, "success")], results)


if __name__ == "__main__":
    unittest.main()
