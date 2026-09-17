import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from services.competitor_monitor import CollectionResult, EnvironmentResult, MonitorStore, normalize_collection
from services.competitor_monitor_auto import AutoMonitor, TaskScheduler
from tests.test_competitor_monitor import complete_raw


class CompetitorMonitorV13Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = MonitorStore(Path(self.temp.name) / "monitor.db")
        self.competitor_id, _ = self.store.add_competitor(
            "https://detail.1688.com/offer/976443859503.html", alias="A404"
        )

    def tearDown(self):
        self.store.close(); self.temp.cleanup()

    def test_auto_run_skips_before_time_and_after_completed_run(self):
        monitor = AutoMonitor(self.store, scheduled_time="09:00")
        self.assertEqual("not_due", monitor.run(now=datetime(2026, 9, 17, 8, 59)))
        run_id = self.store.start_run(1, "scheduled", now="2026-09-17 09:00:00")
        self.store.finish_run(run_id, "completed", 1, now="2026-09-17 09:01:00")
        self.assertEqual("already_completed", monitor.run(now=datetime(2026, 9, 17, 10, 0)))

    def test_auto_run_collects_serially_and_merges_notification_per_product(self):
        baseline = normalize_collection(complete_raw())
        with patch("services.competitor_monitor._now", return_value="2026-09-16 09:00:00"):
            self.store.save_collection(self.competitor_id, CollectionResult("success", baseline))
        changed = complete_raw()
        changed["product"].update({"price_raw_values": ["¥40", "¥50"], "sales_raw": "已售1400+台"})
        changed["skus"].append({"name": "绿色"})
        collector = Mock(); collector.collect.return_value = CollectionResult("success", normalize_collection(changed))
        notifier = Mock()
        monitor = AutoMonitor(
            self.store, environment=Mock(ensure=Mock(return_value=EnvironmentResult(True))),
            collector=collector, notifier=notifier, price_threshold=5, sales_threshold=20,
        )
        with patch("services.competitor_monitor_auto._now", return_value="2026-09-17 09:00:00"):
            self.assertEqual("completed", monitor.run(now=datetime(2026, 9, 17, 9, 0)))
        self.assertEqual(1, collector.collect.call_count)
        notifier.assert_called_once()
        title, body = notifier.call_args.args
        self.assertIn("A404", title)
        self.assertIn("新增SKU", body)
        self.assertIn("展示下界 +100", body)

    def test_environment_failure_is_recorded_and_notified(self):
        notifier = Mock()
        monitor = AutoMonitor(
            self.store, environment=Mock(ensure=Mock(return_value=EnvironmentResult(False, "浏览器失败", "CDP error"))),
            notifier=notifier,
        )
        with patch("services.competitor_monitor_auto._now", return_value="2026-09-17 09:00:00"):
            self.assertEqual("environment_failed", monitor.run(now=datetime(2026, 9, 17, 9, 0)))
        self.assertEqual("environment_failed", self.store.latest_run()["status"])
        notifier.assert_called_once_with("1688竞品监控自动采集失败", "浏览器失败")

    def test_unexpected_collection_failure_is_recorded_and_notified(self):
        collector = Mock(); collector.collect.side_effect = RuntimeError("DOM读取异常")
        notifier = Mock()
        monitor = AutoMonitor(
            self.store, environment=Mock(ensure=Mock(return_value=EnvironmentResult(True))),
            collector=collector, notifier=notifier,
        )
        with patch("services.competitor_monitor_auto._now", return_value="2026-09-17 09:00:00"):
            self.assertEqual("failed", monitor.run(now=datetime(2026, 9, 17, 9, 0)))
        self.assertEqual("failed", self.store.latest_run()["status"])
        notifier.assert_called_once_with("1688竞品监控自动采集失败", "DOM读取异常")

    @patch("services.competitor_monitor_auto.subprocess.run")
    def test_task_scheduler_creates_daily_and_logon_tasks(self, run):
        run.return_value = Mock(returncode=0, stderr="")
        scheduler = TaskScheduler(Path("C:/tool/pythonw.exe"), Path("C:/tool/main.py"))
        scheduler.install("09:00")
        self.assertEqual(2, run.call_count)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertTrue(any("DAILY" in command for command in commands))
        self.assertTrue(any("ONLOGON" in command for command in commands))


if __name__ == "__main__":
    unittest.main()
