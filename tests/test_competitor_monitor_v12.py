import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from services.competitor_monitor import CollectionResult, MonitorStore, normalize_collection
from tests.test_competitor_monitor import complete_raw
from tools.competitor_monitor.page import CompetitorMonitorPage


class CompetitorMonitorV12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = MonitorStore(Path(self.temp.name) / "monitor.db")
        self.competitor_id, _ = self.store.add_competitor(
            "https://detail.1688.com/offer/976443859503.html", alias="A404"
        )

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def save(self, raw, when):
        with patch("services.competitor_monitor._now", return_value=when):
            return self.store.save_collection(
                self.competitor_id, CollectionResult("success", normalize_collection(raw))
            )

    def test_second_snapshot_generates_price_sku_sales_and_metric_events(self):
        self.save(complete_raw(), "2026-09-16 09:00:00")
        changed = complete_raw()
        changed["product"].update({"price_raw_values": ["¥40", "¥50"], "sales_raw": "已售1400+台"})
        changed["skus"] = [{"name": "绿色"}, {"name": "白色"}]
        changed["assistant"]["month_sales_raw"] = "30+"
        self.save(changed, "2026-09-17 09:00:00")

        events = self.store.events()
        self.assertEqual(
            {"price_structure_change", "sku_added", "sales_metric_jump", "metric_change"},
            {row["event_type"] for row in events},
        )
        sales = next(row for row in events if row["event_type"] == "sales_metric_jump")
        self.assertEqual(100, json.loads(sales["detail_json"])["lower_bound_change"])
        self.assertTrue(any("月成交" in row["title"] for row in events))

    def test_single_price_change_has_reliable_percentage(self):
        first = complete_raw(); first["product"]["price_raw_values"] = ["¥100"]
        second = complete_raw(); second["product"]["price_raw_values"] = ["¥90"]
        self.save(first, "2026-09-16 09:00:00")
        self.save(second, "2026-09-17 09:00:00")
        event = self.store.events(event_type="price_change")[0]
        self.assertEqual(-10.0, json.loads(event["detail_json"])["change_percent"])
        self.assertEqual("important", event["severity"])

    def test_matching_price_tier_has_reliable_percentage(self):
        first = complete_raw(); first["product"].update({
            "price_raw_values": ["¥110", "¥100"],
            "price_tiers": [{"qty_raw": "≥1000件", "price_raw": "¥110"}],
        })
        second = complete_raw(); second["product"].update({
            "price_raw_values": ["¥100", "¥95"],
            "price_tiers": [{"qty_raw": "≥1000件", "price_raw": "¥100"}],
        })
        self.save(first, "2026-09-16 09:00:00")
        self.save(second, "2026-09-17 09:00:00")
        detail = json.loads(self.store.events(event_type="price_change")[0]["detail_json"])
        self.assertEqual(-9.09, detail["tier_changes"][0]["change_percent"])

    def test_missing_fields_do_not_create_false_changes(self):
        self.save(complete_raw(), "2026-09-16 09:00:00")
        partial = complete_raw()
        partial["product"]["price_raw_values"] = []
        partial["product"]["sales_raw"] = "unavailable"
        partial["skus"] = []
        self.save(partial, "2026-09-17 09:00:00")
        self.assertEqual({"collection_partial"}, {row["event_type"] for row in self.store.events()})

    def test_daily_history_uses_last_snapshot_without_filling_gaps(self):
        now = datetime.now().replace(microsecond=0)
        first = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        later = (now - timedelta(days=2) + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        self.save(complete_raw(), first)
        changed = complete_raw(); changed["product"]["sales_raw"] = "已售1400+台"
        self.save(changed, later)
        rows = self.store.daily_history(self.competitor_id, 7)
        self.assertEqual(1, len(rows))
        self.assertEqual(1400, rows[0]["sales_lower_bound"])

    def test_dashboard_and_event_views_show_today_changes(self):
        today = datetime.now().strftime("%Y-%m-%d 09:00:00")
        self.save(complete_raw(), today)
        changed = complete_raw(); changed["skus"].append({"name": "绿色"})
        self.save(changed, today)
        page = CompetitorMonitorPage(self.store.path)
        try:
            self.assertIn("SKU变化 1", page.summary.text())
            self.assertEqual(1, page.events_table.rowCount())
            page.table.selectRow(0)
            page.open_history()
            self.assertIsNotNone(page.history_dialog)
        finally:
            page.store.close()


if __name__ == "__main__":
    unittest.main()
