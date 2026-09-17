import json
import tempfile
import unittest
from pathlib import Path

from services.competitor_monitor import CollectionResult, MonitorStore, normalize_collection, parse_metric, parse_offer_url


def complete_raw():
    return {
        "product": {"title": "暖手宝", "price_raw_values": ["¥45", "¥50"], "price_tiers": [],
                    "min_order_qty": "1台起批", "sales_raw": "已售1300+台"},
        "assistant": {"listed_at": "2025-09-16", "month_sales_raw": "20+", "month_distribution_raw": "10+",
                      "year_sales_quantity_raw": "1300+", "year_sales_orders_raw": "1200+",
                      "review_count_raw": "3", "positive_rate_raw": "100%"},
        "skus": [{"name": "白色", "selected": True, "specification_raw": "6000mAh", "price_raw": "¥48", "availability": "available", "stock_raw": "库存10台"}],
    }


class CompetitorMonitorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = MonitorStore(Path(self.temp.name) / "monitor.db")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_url_validation_and_duplicate_offer(self):
        self.assertEqual(("976443859503", "https://detail.1688.com/offer/976443859503.html"),
                         parse_offer_url("https://detail.1688.com/offer/976443859503.html?spm=x"))
        with self.assertRaises(ValueError):
            parse_offer_url("https://example.com/offer/976443859503.html")
        first = self.store.add_competitor("https://detail.1688.com/offer/976443859503.html")
        second = self.store.add_competitor("https://detail.1688.com/offer/976443859503.html?x=1")
        self.assertEqual((first[0], False), second)

    def test_groups_delete_to_ungrouped(self):
        group_id = self.store.add_group("暖手宝")
        competitor_id, _ = self.store.add_competitor("https://detail.1688.com/offer/976443859503.html", group_id)
        self.store.rename_group(group_id, "小家电")
        self.assertEqual("小家电", self.store.competitors()[0]["group_name"])
        self.store.delete_group(group_id)
        self.assertIsNone(self.store.competitor(competitor_id)["group_id"])

    def test_complete_and_partial_snapshots_are_kept(self):
        competitor_id, _ = self.store.add_competitor("https://detail.1688.com/offer/976443859503.html")
        data = normalize_collection(complete_raw())
        self.assertEqual("success", data["collection_status"])
        self.store.save_collection(competitor_id, CollectionResult("success", data))
        partial_raw = complete_raw(); partial_raw["assistant"]["month_sales_raw"] = "unavailable"
        partial = normalize_collection(partial_raw)
        self.store.save_collection(competitor_id, CollectionResult("partial", partial))
        latest = self.store.latest_snapshot(competitor_id)
        self.assertEqual("partial", latest["collection_status"])
        self.assertEqual(["month_sales_raw"], json.loads(latest["missing_fields_json"]))
        self.assertEqual(2, self.store.competitors()[0]["snapshot_count"])
        self.assertEqual("部分异常", self.store.competitor(competitor_id)["status"])
        self.assertEqual((45.0, 50.0, 1300, "gte", "6000mAh"),
                         (latest["display_price_min"], latest["display_price_max"], latest["sales_lower_bound"],
                          latest["sales_value_type"], latest["selected_sku_name"]))

    def test_fuzzy_metric_keeps_semantics(self):
        self.assertEqual((0, "lt"), parse_metric("<10"))
        self.assertEqual((12000, "gte"), parse_metric("已售1.2万+件"))

    def test_failed_collection_keeps_existing_snapshot(self):
        competitor_id, _ = self.store.add_competitor("https://detail.1688.com/offer/976443859503.html")
        data = normalize_collection(complete_raw())
        self.store.save_collection(competitor_id, CollectionResult("success", data))
        self.store.save_collection(competitor_id, CollectionResult("failed", error="Chrome无法连接"))
        self.assertIsNotNone(self.store.latest_snapshot(competitor_id))
        self.assertEqual("采集失败", self.store.competitor(competitor_id)["status"])
        self.assertEqual("Chrome无法连接", self.store.latest_failure(competitor_id))


if __name__ == "__main__":
    unittest.main()
