import tempfile
import unittest
from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, QSettings
from PySide6.QtWidgets import QAbstractItemView, QAbstractSpinBox, QApplication, QScrollArea, QTableWidget

from app.theme import STYLE
from tests.test_order_calendar import y35_plan
from tools.order_calendar.page import OrderCalendarPage, PlanDialog, TaskDialog
from tools.order_calendar.widgets import NumberInput


class OrderCalendarUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion")
        cls.app.setStyleSheet(STYLE)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "order_calendar").clear()
        self.page = OrderCalendarPage(Path(self.temp.name) / "order_calendar.json")
        self.page.calendar_data.add_plan(y35_plan())
        self.page.calendar.setCurrentPage(2026, 9)
        self.page.refresh()

    def tearDown(self) -> None:
        self.page.close()
        self.temp.cleanup()

    def test_calendar_is_primary_view_and_shows_schedule(self) -> None:
        self.assertEqual(date.today(), self.page.selected_day)
        self.assertGreater(self.page.calendar.width(), 0)
        self.assertEqual(("jd", "Y35"), (self.page.calendar.tasks["2026-09-16"][0]["platform"], self.page.calendar.tasks["2026-09-16"][0]["model"]))

    def test_one_click_completion_and_review_are_saved_immediately(self) -> None:
        task = self.page.calendar_data.tasks_between(date(2026, 9, 16), date(2026, 9, 16))[0]
        self.page.complete(task)
        saved = self.page.calendar_data.record_for("plan_y35", date(2026, 9, 16))
        self.assertEqual(1, saved["actual_quantity"])
        self.page.mark_reviewed(self.page.calendar_data.tasks_between(date(2026, 9, 16), date(2026, 9, 16))[0])
        saved = self.page.calendar_data.record_for("plan_y35", date(2026, 9, 16))
        self.assertEqual((1, date.today().isoformat()), (saved["reviewed_quantity"], saved["review_date"]))

    def test_plan_dialog_uses_platform_model_and_custom_controls(self) -> None:
        dialog = PlanDialog(self.page.calendar_data, parent=self.page)
        self.assertIsNone(dialog.findChild(QTableWidget))
        self.assertEqual(3, len(dialog.stages.cards))
        self.assertTrue(all(isinstance(card.frequency, NumberInput) for card in dialog.stages.cards))
        self.assertTrue(all(card.frequency.buttonSymbols() == QAbstractSpinBox.ButtonSymbols.NoButtons for card in dialog.stages.cards))
        self.assertEqual("jd", dialog.platform.currentData())
        dialog.model.setText("Y35")
        self.assertEqual("continuous", dialog.stages.cards[-1].kind.currentData())
        self.assertFalse(dialog.stages.add_button.isEnabled())
        dialog.close()

    def test_custom_date_input_validates_keyboard_text(self) -> None:
        dialog = PlanDialog(self.page.calendar_data, parent=self.page)
        dialog.start_date.input.setText("2026/09/16")
        dialog.start_date._parse()
        self.assertTrue(dialog.start_date.is_valid())
        self.assertEqual(QDate(2026, 9, 16), dialog.start_date.date())
        dialog.start_date.input.setText("2026/02/31")
        dialog.start_date._parse()
        self.assertFalse(dialog.start_date.is_valid())
        dialog.close()

    def test_stage_validation_and_complete_plan_save_flow(self) -> None:
        dialog = PlanDialog(self.page.calendar_data, parent=self.page)
        dialog.model.setText("X6")
        dialog.start_date.setDate(QDate(2026, 9, 16))
        until = dialog.stages.cards[1]
        until.value_input.setValue(3)
        self.assertFalse(dialog.stages.validate(0))
        self.assertIn("必须大于", until.error.text())
        until.value_input.setValue(10)
        dialog._save()
        saved = self.page.calendar_data.plans[-1]
        self.assertEqual(("jd", "X6", "2026-09-16"), (saved["platform"], saved["model"], saved["start_date"]))
        self.assertEqual(["fixed_count", "until_total", "continuous"], [stage["type"] for stage in saved["stages"]])

        reopened = PlanDialog(self.page.calendar_data, saved, self.page)
        self.assertEqual(["fixed_count", "until_total", "continuous"], [card.kind.currentData() for card in reopened.stages.cards])
        self.assertEqual([3, 10], [reopened.stages.cards[0].value_input.value(), reopened.stages.cards[1].value_input.value()])
        reopened._save()
        self.assertEqual([3, 10], [saved["stages"][0]["count"], saved["stages"][1]["until_total"]])

    def test_platform_filter_updates_calendar_statistics_detail_and_reviews(self) -> None:
        self.page.resize(1000, 800)
        self.page.show()
        QApplication.processEvents()
        calendar_height = self.page.calendar.height()
        self.page.calendar_data.add_plan(y35_plan("1688", "plan_1688_y35"))
        self.page.calendar_data.upsert_record("plan_y35", date(2026, 9, 16), actual_quantity=1)
        self.page.calendar_data.upsert_record("plan_1688_y35", date(2026, 9, 16), actual_quantity=1)
        self.page.platform_filter.setCurrentIndex(self.page.platform_filter.findData("jd"))
        self.page.refresh()
        QApplication.processEvents()
        self.assertEqual(1, len(self.page.calendar.tasks["2026-09-16"]))
        self.assertEqual(calendar_height, self.page.calendar.height())
        self.assertEqual("jd", self.page.calendar.tasks["2026-09-16"][0]["platform"])
        self.assertEqual(["1", "1", "0", "1"], [label.text() for label in self.page.stats])
        self.page.platform_filter.setCurrentIndex(self.page.platform_filter.findData("all"))
        self.page.refresh()
        QApplication.processEvents()
        self.assertEqual(2, len(self.page.calendar.tasks["2026-09-16"]))
        self.assertEqual(calendar_height, self.page.calendar.height())
        self.assertEqual(["2", "2", "0", "2"], [label.text() for label in self.page.stats])

    def test_manual_task_saves_platform_and_model_without_plan(self) -> None:
        dialog = TaskDialog(self.page.calendar_data, date(2026, 9, 25), parent=self.page)
        dialog.platform.setCurrentIndex(dialog.platform.findData("1688"))
        dialog.model.setText("A404")
        dialog._save()
        record = next(item for item in self.page.calendar_data.records if item.get("plan_id") is None)
        self.assertEqual(("manual", "1688", "A404"), (record["source"], record["platform"], record["model"]))

    def test_pending_review_count_does_not_resize_calendar(self) -> None:
        self.page.resize(1000, 800)
        self.page.show()
        QApplication.processEvents()
        baseline = self.page.calendar.height()

        for count in range(20):
            self.page.calendar_data.upsert_record(
                None, date(2026, 9, count + 1), source="manual", platform="jd",
                model=f"SKU-{count}", target_quantity=1, actual_quantity=1,
            )
            if count in (0, 5, 19):
                self.page.refresh()
                QApplication.processEvents()
                self.assertEqual(baseline, self.page.calendar.height())

        self.assertEqual("20", self.page.review_count.text())
        self.assertTrue(self.page.review_area.verticalScrollBar().maximum() > 0)
        self.assertLessEqual(self.page.review_area.height(), self.page.review_area.maximumHeight())

        grid = self.page.calendar.findChild(QAbstractItemView)
        self.assertEqual((7, 7), (grid.model().rowCount(), grid.model().columnCount()))
        self.page.calendar.showNextMonth()
        QApplication.processEvents()
        self.assertEqual(baseline, self.page.calendar.height())

    def test_small_window_scrolls_instead_of_shrinking_calendar(self) -> None:
        self.page.resize(1000, 450)
        self.page.show()
        QApplication.processEvents()
        page_scroll = self.page.findChild(QScrollArea, "orderCalendarPageScroll")
        self.assertGreaterEqual(self.page.calendar.height(), 300)
        self.assertGreater(page_scroll.verticalScrollBar().maximum(), 0)


if __name__ == "__main__":
    unittest.main()
