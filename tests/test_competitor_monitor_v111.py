import tempfile
import unittest
import sqlite3
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QPlainTextEdit, QPushButton, QStackedLayout

from services.competitor_monitor import (
    ChromeEnvironment, CollectionResult, EnvironmentResult, MonitorStore,
    PlaywrightCollector, normalize_collection,
)
from tests.test_competitor_monitor import complete_raw
from tools.competitor_monitor.page import CollectionProgress, GroupManagerDialog, MessageDialog
from tools.competitor_monitor.worker import CollectionWorker


URL = "https://detail.1688.com/offer/976443859503.html"


class CompetitorMonitorV111Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_cdp_does_not_start_chrome(self):
        environment = ChromeEnvironment()
        with patch.object(environment, "is_ready", return_value=True), patch.object(environment, "_start_chrome") as start:
            self.assertTrue(environment.ensure().ready)
        start.assert_not_called()

    def test_missing_cdp_starts_chrome_and_waits_until_ready(self):
        environment = ChromeEnvironment()
        with patch.object(environment, "is_ready", side_effect=[False, False, True]), \
             patch.object(environment, "_start_chrome") as start, patch("services.competitor_monitor.time.sleep"):
            self.assertTrue(environment.ensure().ready)
        start.assert_called_once_with()

    def test_chrome_start_failure_is_task_error(self):
        environment = ChromeEnvironment()
        with patch.object(environment, "is_ready", return_value=False), \
             patch.object(environment, "_start_chrome", side_effect=FileNotFoundError("chrome.exe")):
            result = environment.ensure()
        self.assertFalse(result.ready)
        self.assertIn("浏览器启动失败", result.error)
        self.assertIn("chrome.exe", result.technical_error)

    def test_recoverable_failure_retries_once_then_succeeds(self):
        collector = PlaywrightCollector()
        success = CollectionResult("success", normalize_collection(complete_raw()))
        with patch.object(collector, "_collect_once", side_effect=[
            CollectionResult("failed", error="商品数据未完整加载", recoverable=True), success,
        ]) as collect_once, patch("services.competitor_monitor.time.sleep") as sleep:
            result = collector.collect(URL)
        self.assertEqual("success", result.status)
        self.assertEqual(2, collect_once.call_count)
        sleep.assert_called_once_with(2)

    def test_two_recoverable_failures_stop_after_second(self):
        collector = PlaywrightCollector()
        failed = CollectionResult("failed", error="官方采购助手未加载", recoverable=True)
        with patch.object(collector, "_collect_once", side_effect=[failed, failed]) as collect_once, \
             patch("services.competitor_monitor.time.sleep"):
            result = collector.collect(URL)
        self.assertEqual("failed", result.status)
        self.assertEqual(2, collect_once.call_count)

    def test_deterministic_failure_does_not_retry(self):
        collector = PlaywrightCollector()
        failed = CollectionResult("failed", error="1688商品不存在或已下架")
        with patch.object(collector, "_collect_once", return_value=failed) as collect_once:
            self.assertEqual("failed", collector.collect(URL).status)
        collect_once.assert_called_once_with(URL)

    def test_environment_and_login_failures_do_not_emit_item_results(self):
        item = {"id": 1, "url": URL, "offer_id": "976443859503", "alias": None, "title": None}
        for environment_result, collection_result in (
            (EnvironmentResult(False, "启动失败", "raw"), None),
            (EnvironmentResult(True), CollectionResult("failed", error="登录失效", environment_error=True)),
        ):
            completed, environment_errors = [], []
            with patch("tools.competitor_monitor.worker.ChromeEnvironment.is_ready", return_value=environment_result.ready), \
                 patch("tools.competitor_monitor.worker.ChromeEnvironment.ensure", return_value=environment_result), \
                 patch("tools.competitor_monitor.worker.PlaywrightCollector.collect", return_value=collection_result):
                worker = CollectionWorker([item], "http://127.0.0.1:9222")
                worker.item_completed.connect(lambda *args: completed.append(args))
                worker.environment_failed.connect(lambda *args: environment_errors.append(args))
                worker.run()
            self.assertEqual([], completed)
            self.assertEqual(1, len(environment_errors))

    def test_shop_name_is_optional_and_missing_value_does_not_clear_existing(self):
        with tempfile.TemporaryDirectory() as name:
            store = MonitorStore(Path(name) / "monitor.db")
            competitor_id, _ = store.add_competitor(URL)
            first = normalize_collection(complete_raw())
            store.save_collection(competitor_id, CollectionResult("success", first))
            self.assertEqual("佛山淘趣科技有限公司", store.competitor(competitor_id)["shop_name"])
            raw = complete_raw(); raw["page_metadata"]["merchant_raw"] = "unavailable"
            second = normalize_collection(raw)
            self.assertEqual("success", second["collection_status"])
            store.save_collection(competitor_id, CollectionResult("success", second))
            self.assertEqual("佛山淘趣科技有限公司", store.competitor(competitor_id)["shop_name"])
            store.close()

    def test_existing_v11_database_adds_shop_name_column(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "monitor.db"
            db = sqlite3.connect(path)
            db.execute("""CREATE TABLE competitors (
                id INTEGER PRIMARY KEY, offer_id TEXT NOT NULL UNIQUE, url TEXT NOT NULL,
                title TEXT, alias TEXT, group_id INTEGER, note TEXT, monitor_enabled INTEGER,
                status TEXT, created_at TEXT, last_success_at TEXT, last_attempt_at TEXT
            )""")
            db.commit(); db.close()
            store = MonitorStore(path)
            columns = {row["name"] for row in store.db.execute("PRAGMA table_info(competitors)")}
            self.assertIn("shop_name", columns)
            store.close()

    def test_progress_percentages_are_complete_and_dialog_is_wide(self):
        dialog = CollectionProgress(10)
        self.assertGreaterEqual(dialog.minimumWidth(), 650)
        for completed, expected in ((0, "0%"), (1, "10%"), (6, "60%"), (8, "80%"), (10, "100%")):
            dialog.update_progress(completed, 10)
            self.assertEqual(expected, dialog.percent.text())
        self.assertGreaterEqual(dialog.bar.minimumHeight(), 26)
        self.assertIs(dialog.percent, dialog.findChild(QStackedLayout).currentWidget())
        dialog.set_current(4, 5, "商品" * 100)
        self.assertIn("正在监控 4 / 5", dialog.label.text())
        self.assertTrue(dialog.label.text().endswith("…"))

    def test_custom_dialogs_have_chinese_buttons_and_hidden_details(self):
        message = MessageDialog("错误", "用户信息", details="ECONNREFUSED")
        self.assertTrue(any(button.text() == "查看详情" for button in message.findChildren(QPushButton)))
        self.assertFalse(any(button.text() in {"OK", "Cancel"} for button in message.findChildren(QPushButton)))
        self.assertTrue(message.findChildren(QPlainTextEdit)[0].isHidden())
        with tempfile.TemporaryDirectory() as name:
            store = MonitorStore(Path(name) / "monitor.db")
            groups = GroupManagerDialog(store)
            self.assertFalse(any(button.text() in {"OK", "Cancel"} for button in groups.findChildren(QPushButton)))
            store.close()


if __name__ == "__main__":
    unittest.main()
