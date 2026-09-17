import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from services.competitor_monitor import CollectionResult, normalize_collection
from tests.test_competitor_monitor import complete_raw
from tools.competitor_monitor.page import CompetitorMonitorPage


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
        self.assertEqual(("A404", "佛山淘趣科技有限公司", "¥45 / ¥50", "正常"),
                         tuple(self.page.table.item(0, column).text() for column in (0, 1, 3, 9)))
        self.assertIn("白色", self.page.detail.text())
        self.page.toggle_selected()
        self.assertEqual("暂停", self.page.store.competitor(competitor_id)["status"])


if __name__ == "__main__":
    unittest.main()
