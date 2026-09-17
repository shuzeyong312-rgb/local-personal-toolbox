import unittest
from unittest.mock import patch

from services.competitor_monitor import CollectionResult
from services.competitor_monitor_collection import PlaywrightCollector, normalize_collection
from tests.test_competitor_monitor import complete_raw


URL = "https://detail.1688.com/offer/976443859503.html"


class CompetitorCollectionPolicyTests(unittest.TestCase):
    def test_auxiliary_field_missing_does_not_mark_snapshot_partial(self):
        raw = complete_raw()
        raw["assistant"]["listed_at"] = "unavailable"
        raw["assistant"]["month_distribution_raw"] = "unavailable"
        raw["assistant"]["year_sales_orders_raw"] = "unavailable"

        data = normalize_collection(raw)

        self.assertEqual("success", data["collection_status"])
        self.assertEqual([], data["missing_fields"])
        self.assertIn("listed_at", data["auxiliary_missing_fields"])
        self.assertIn("month_distribution_raw", data["auxiliary_missing_fields"])
        self.assertIn("year_sales_orders_raw", data["auxiliary_missing_fields"])

    def test_basic_field_missing_does_not_mark_snapshot_partial(self):
        raw = complete_raw()
        raw["product"]["min_order_qty"] = "unavailable"

        data = normalize_collection(raw)

        self.assertEqual("success", data["collection_status"])
        self.assertEqual([], data["missing_fields"])
        self.assertEqual(["min_order_qty"], data["basic_missing_fields"])

    def test_monitor_field_missing_marks_snapshot_partial(self):
        raw = complete_raw()
        raw["product"]["sales_raw"] = "unavailable"

        data = normalize_collection(raw)

        self.assertEqual("partial", data["collection_status"])
        self.assertEqual(["sales_raw"], data["missing_fields"])

    def test_any_partial_monitor_snapshot_retries_once(self):
        collector = PlaywrightCollector()
        partial_data = normalize_collection({
            **complete_raw(),
            "product": {**complete_raw()["product"], "sales_raw": "unavailable"},
        })
        success_data = normalize_collection(complete_raw())
        partial = CollectionResult("partial", data=partial_data, recoverable=True)
        success = CollectionResult("success", data=success_data)

        with patch.object(collector, "_collect_once", side_effect=[partial, success]) as collect_once, \
             patch("services.competitor_monitor_collection.time.sleep") as sleep:
            result = collector.collect(URL)

        self.assertEqual("success", result.status)
        self.assertEqual(2, collect_once.call_count)
        sleep.assert_called_once_with(2)

    def test_success_with_auxiliary_gaps_does_not_retry(self):
        raw = complete_raw()
        raw["assistant"]["listed_at"] = "unavailable"
        data = normalize_collection(raw)
        result = CollectionResult("success", data=data, recoverable=False)
        collector = PlaywrightCollector()

        with patch.object(collector, "_collect_once", return_value=result) as collect_once, \
             patch("services.competitor_monitor_collection.time.sleep") as sleep:
            final = collector.collect(URL)

        self.assertEqual("success", final.status)
        collect_once.assert_called_once_with(URL)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
