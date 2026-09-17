import unittest
from unittest.mock import patch

from services.competitor_monitor import CollectionResult
from services.competitor_monitor_collection import (
    PlaywrightCollector,
    _is_target_offer_url,
    _is_verification_probe,
    merge_raw_samples,
    normalize_collection,
)
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

    def test_sold_count_missing_is_optional_when_stable_monitor_fields_exist(self):
        raw = complete_raw()
        raw["product"]["sales_raw"] = "unavailable"
        raw["product"]["interest_raw"] = "50+人想买"

        data = normalize_collection(raw)

        self.assertEqual("success", data["collection_status"])
        self.assertEqual([], data["missing_fields"])
        self.assertEqual("50+人想买", data["interest_raw"])
        self.assertIn("sales_raw", data["optional_dynamic_missing_fields"])

    def test_stable_monitor_field_missing_marks_snapshot_partial(self):
        raw = complete_raw()
        raw["assistant"]["month_sales_raw"] = "unavailable"

        data = normalize_collection(raw)

        self.assertEqual("partial", data["collection_status"])
        self.assertEqual(["month_sales_raw"], data["missing_fields"])

    def test_rotating_samples_keep_both_sold_and_interest_values(self):
        sold = complete_raw()
        sold["product"]["sales_raw"] = "已售20+台"
        sold["product"]["interest_raw"] = "unavailable"
        sold["unavailable_reasons"] = {
            "product.interest_raw": "销量/想买轮播位当前显示已售，当前帧未显示想买人数"
        }

        interest = complete_raw()
        interest["product"]["sales_raw"] = "unavailable"
        interest["product"]["interest_raw"] = "50+人想买"
        interest["unavailable_reasons"] = {
            "product.sales_raw": "销量/想买轮播位当前显示想买人数，当前帧未显示已售"
        }

        merged = merge_raw_samples([sold, interest])

        self.assertEqual("已售20+台", merged["product"]["sales_raw"])
        self.assertEqual("50+人想买", merged["product"]["interest_raw"])
        self.assertNotIn("product.sales_raw", merged["unavailable_reasons"])
        self.assertNotIn("product.interest_raw", merged["unavailable_reasons"])
        self.assertEqual(
            {"samples": 2, "sales_seen": True, "interest_seen": True},
            merged["carousel_observations"],
        )

    def test_any_partial_stable_monitor_snapshot_retries_once(self):
        raw = complete_raw()
        raw["assistant"]["month_sales_raw"] = "unavailable"
        partial_data = normalize_collection(raw)
        success_data = normalize_collection(complete_raw())
        partial = CollectionResult("partial", data=partial_data, recoverable=True)
        success = CollectionResult("success", data=success_data)

        collector = PlaywrightCollector()
        with patch.object(collector, "_collect_once", side_effect=[partial, success]) as collect_once, \
             patch("services.competitor_monitor_collection.time.sleep") as sleep:
            result = collector.collect(URL)

        self.assertEqual("success", result.status)
        self.assertEqual(2, collect_once.call_count)
        sleep.assert_called_once_with(2)

    def test_success_with_optional_dynamic_gap_does_not_retry(self):
        raw = complete_raw()
        raw["product"]["sales_raw"] = "unavailable"
        raw["product"]["interest_raw"] = "10+人想买"
        data = normalize_collection(raw)
        result = CollectionResult("success", data=data, recoverable=False)
        collector = PlaywrightCollector()

        with patch.object(collector, "_collect_once", return_value=result) as collect_once, \
             patch("services.competitor_monitor_collection.time.sleep") as sleep:
            final = collector.collect(URL)

        self.assertEqual("success", final.status)
        collect_once.assert_called_once_with(URL)
        sleep.assert_not_called()

    def test_verification_probe_requires_strong_evidence_and_ignores_normal_product(self):
        self.assertFalse(_is_verification_probe({"normal_product": True, "phrases": ["安全验证"]}))
        self.assertFalse(_is_verification_probe({"normal_product": False, "access_abnormal": True}))
        self.assertTrue(_is_verification_probe({"normal_product": False, "phrases": ["请完成验证"]}))
        self.assertTrue(_is_verification_probe({"normal_product": False, "selectors": ["[class*=captcha]"], "risk_url": True}))

    def test_verification_recovery_requires_the_original_offer_not_home_page(self):
        self.assertTrue(_is_target_offer_url(URL, URL))
        self.assertFalse(_is_target_offer_url("https://www.1688.com/", URL))
        self.assertFalse(_is_target_offer_url("https://detail.1688.com/offer/1.html", URL))

    def test_needs_verification_never_uses_normal_retry(self):
        collector = PlaywrightCollector()
        verification = CollectionResult("needs_verification")
        with patch.object(collector, "_collect_once", return_value=verification) as collect_once, \
             patch("services.competitor_monitor_collection.time.sleep") as sleep:
            result = collector.collect(URL)

        self.assertEqual("needs_verification", result.status)
        collect_once.assert_called_once_with(URL)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
