import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QTime
from PySide6.QtWidgets import QApplication, QLabel, QToolButton

from services.competitor_monitor import CollectionResult, normalize_collection
from tests.test_competitor_monitor import complete_raw
from tools.competitor_monitor.page import CompetitorMonitorPage, MonitorNumberField, MonitorTimeField, ProductCell, format_event_parts


class CompetitorMonitorUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.page = CompetitorMonitorPage(Path(self.temp.name) / "monitor.db")

    def tearDown(self):
        self.page.store.close()
        self.temp.cleanup()

    def test_latest_snapshot_is_visible_and_pause_is_preserved(self):
        competitor_id, _ = self.page.store.add_competitor(
            "https://detail.1688.com/offer/976443859503.html", alias="A404"
        )
        self.page.store.save_collection(
            competitor_id, CollectionResult("success", normalize_collection(complete_raw()))
        )
        self.page.refresh(); self.page.table.selectRow(0); self.page.show_latest()
        self.assertEqual(("A404", "¥45 – ¥50", "已售1300+台", "正常"),
                         tuple(self.page.table.item(0, column).text() for column in (0, 1, 2, 6)))
        self.assertIn("佛山淘趣科技有限公司 · 未分组", self.page.table.cellWidget(0, 0).text())
        self.assertIn("白色", self.page.detail.text())
        self.page.toggle_selected()
        self.assertEqual("暂停", self.page.store.competitor(competitor_id)["status"])

    def test_price_event_is_presented_as_business_text(self):
        event = {"title": "价格变化", "detail_json": '{"before":["¥45.00"],"after":["¥50.00"],"change_percent":11.11}'}
        self.assertEqual(("¥45.00 → ¥50.00", "+¥5 / +11.1%"), format_event_parts(event))

    def test_long_product_name_is_capped_at_two_lines_with_full_tooltip(self):
        name = "超长竞品名称" * 12
        cell = ProductCell(name, "店铺", "未分组")
        cell.resize(260, 72)
        self.assertLessEqual(cell.title.text().count("\n") + 1, 2)
        self.assertTrue(cell.title.text().endswith("…"))
        self.assertIn(name, cell.toolTip())

    def test_monitor_time_field_has_no_native_spin_buttons(self):
        self.assertIsInstance(self.page.scheduled_time, MonitorTimeField)
        self.page.scheduled_time.setText("18:30")
        self.page.scheduled_time.editingFinished.emit()
        self.assertEqual(QTime(18, 30), self.page.scheduled_time.time())

    def test_monitor_number_field_clamps_and_keeps_suffix(self):
        field = MonitorNumberField()
        field.setRange(0.1, 100); field.setSuffix(" %"); field.setValue(5)
        field.setText("300 %"); field.editingFinished.emit()
        self.assertEqual(100, field.value())
        self.assertEqual("100 %", field.text())


if __name__ == "__main__":
    unittest.main()
