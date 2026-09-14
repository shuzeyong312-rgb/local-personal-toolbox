import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QSplitter, QWidget

from app.main_window import MainWindow
from app.theme import STYLE
from tools.background_remove.page import BackgroundRemovePage
from components.controls import AppComboBox, AppSpinBox
from components.dialogs import TaskDialog
from tools.watermark.page import WatermarkPage
from tools.resize.page import ResizePage
from tools.rename.page import RenamePage


class UiStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.settings_dir = tempfile.TemporaryDirectory()
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, cls.settings_dir.name)
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion")
        cls.app.setStyleSheet(STYLE)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.settings_dir.cleanup()

    def setUp(self) -> None:
        QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "watermark").clear()
        QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "resize").clear()
        QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "rename").clear()
        QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "background_remove").clear()

    def test_background_remove_page_defaults_and_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            source = Path(name) / "商品.png"
            Image.new("RGB", (40, 30), "white").save(source)
            page = BackgroundRemovePage()
            self.assertEqual("standard", page.mode.currentData())
            self.assertTrue(page.soften_edges.isChecked())
            self.assertEqual("processed", page.preview_state.currentData())
            page.add_files([source])
            page.update_preview()
            self.assertTrue(page.start_button.isEnabled())
            self.assertIn("40 × 30", page.image_info.text())

            window = MainWindow()
            self.assertEqual(["批量打水印", "修改图片尺寸", "白底转透明", "批量重命名"],
                             [window.navigation.item(i).text() for i in range(window.navigation.count())])
            window.close()

    def test_rename_preview_conflict_and_settings(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            first, second = root / "uuid-b.png", root / "uuid-a.jpg"
            first.write_text("b", encoding="utf-8")
            second.write_text("a", encoding="utf-8")
            os.utime(first, (100, 100))
            os.utime(second, (100, 100))
            page = RenamePage()
            self.assertFalse(page.start_button.isEnabled())
            page.add_files([first, second])
            self.assertEqual("uuid-a.jpg", page.table.item(0, 0).text())
            self.assertEqual("详情页_1.jpg", page.table.item(0, 2).text())
            self.assertTrue(page.start_button.isEnabled())
            page.digits.setCurrentIndex(1)
            self.assertEqual("详情页_01.jpg", page.table.item(0, 2).text())
            page.prefix.setText("商品_")
            restored = RenamePage()
            self.assertEqual("商品_", restored.prefix.text())
            self.assertEqual(1, restored.digits.currentIndex())
            occupied = root / "商品_01.jpg"
            occupied.write_text("keep", encoding="utf-8")
            page.refresh_preview()
            self.assertFalse(page.start_button.isEnabled())
            self.assertIn("目标文件已存在", page.error_label.text())
            page.resize(860, 652)
            page.show()
            self.app.processEvents()
            self.assertLessEqual(page.start_button.mapTo(page, page.start_button.rect().bottomLeft()).y(), page.height())
            page.close()

    def test_resize_page_modes_preview_settings_and_locking(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            source = Path(name) / "product.png"
            Image.new("RGB", (1600, 1200), "red").save(source)
            page = ResizePage()
            self.assertFalse(page.start_button.isEnabled())
            page.add_files([source])
            page.update_preview()
            self.assertIn("预计输出 800 × 800", page.image_info.text())
            page.mode.setCurrentIndex(page.mode.findData("width"))
            self.assertTrue(page.width_field.isVisibleTo(page))
            self.assertFalse(page.height_field.isVisibleTo(page))
            page.mode.setCurrentIndex(page.mode.findData("height"))
            self.assertFalse(page.width_field.isVisibleTo(page))
            self.assertTrue(page.height_field.isVisibleTo(page))
            page.mode.setCurrentIndex(page.mode.findData("fixed"))
            page.fit_mode.setCurrentIndex(page.fit_mode.findData("contain"))
            self.assertTrue(page.color_field.isVisibleTo(page))
            page.fit_mode.setCurrentIndex(page.fit_mode.findData("cover"))
            self.assertFalse(page.color_field.isVisibleTo(page))
            before = page.width_input.value()
            event = QWheelEvent(QPointF(5, 5), QPointF(5, 5), QPoint(), QPoint(0, 120), Qt.MouseButton.NoButton,
                                Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.ScrollUpdate, False)
            page.width_input.wheelEvent(event)
            self.assertEqual(before, page.width_input.value())
            page.width_input.setValue(1234)
            restored = ResizePage()
            self.assertEqual(1234, restored.width_input.value())
            self.assertEqual([], restored.sources)
            page._set_processing(True)
            self.assertFalse(page.settings_card.isEnabled())
            page.resize(860, 652)
            page.show()
            self.app.processEvents()
            self.assertLessEqual(page.start_button.mapTo(page, page.start_button.rect().bottomLeft()).y(), page.height())
            page.close()

    def test_start_button_and_single_remove_follow_file_state(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            source = Path(name) / "测试图片.png"
            Image.new("RGB", (20, 20), "white").save(source)
            page = WatermarkPage()
            self.assertFalse(page.start_button.isEnabled())
            page.add_files([source])
            self.assertEqual("开始处理 1 张图片", page.start_button.text())
            self.assertTrue(page.start_button.isEnabled())
            page.text_input.clear()
            self.assertFalse(page.start_button.isEnabled())
            page._remove_item(page.file_list.item(0))
            self.assertEqual([], page.sources)

    def test_main_window_uses_frameless_custom_title_bar(self) -> None:
        window = MainWindow()
        self.assertTrue(window.windowFlags() & Qt.WindowType.FramelessWindowHint)
        self.assertIs(window, window.title_bar.window())
        self.assertEqual((1080, 700), (window.minimumWidth(), window.minimumHeight()))
        window.resize(1080, 700)
        window.show()
        self.app.processEvents()
        splitter = window.findChild(QSplitter, "workspaceSplitter")
        self.assertGreaterEqual(splitter.widget(0).width(), 400)
        self.assertGreaterEqual(splitter.widget(1).width(), 340)
        self.assertTrue(window.watermark_page.start_button.isVisible())
        window.close()

    def test_parameter_controls_ignore_wheel_changes(self) -> None:
        page = WatermarkPage()
        self.assertIsInstance(page.font_size, AppSpinBox)
        self.assertIsInstance(page.position, AppComboBox)
        controls = (page.font_size, page.opacity, page.position, page.margin, page.angle, page.spacing)
        before = [control.value() if hasattr(control, "value") else control.currentIndex() for control in controls]
        for control in controls:
            event = QWheelEvent(
                QPointF(5, 5),
                QPointF(5, 5),
                QPoint(),
                QPoint(0, 120),
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
                Qt.ScrollPhase.ScrollUpdate,
                False,
            )
            control.wheelEvent(event)
        after = [control.value() if hasattr(control, "value") else control.currentIndex() for control in controls]
        self.assertEqual(before, after)
        self.assertFalse(page.font_size.grab().isNull())
        self.assertFalse(page.position.grab().isNull())
        self.assertGreaterEqual(page.opacity.minimumHeight(), 28)

    def test_task_dialog_switches_from_progress_to_result(self) -> None:
        dialog = TaskDialog(5, Path("output"))
        self.assertTrue(dialog.isModal())
        dialog.update_progress(3, 5, 2, 1)
        self.assertEqual(3, dialog.progress.value())
        self.assertEqual("已处理 3 / 总数 5", dialog.progress_count.text())
        self.assertEqual((2, 1), (dialog.success, dialog.failed))
        dialog.reject()
        self.assertTrue(dialog.processing)

        dialog.show_result(4, 1, ["bad.png: damaged"])
        self.assertFalse(dialog.processing)
        self.assertEqual("处理完成", dialog.windowTitle())
        self.assertEqual("成功 4 张", dialog.success_label.text())
        self.assertEqual("失败 1 张", dialog.failure_label.text())
        self.assertEqual("output", dialog.output_name.text())
        self.assertEqual("output", dialog.output_path.text())
        self.assertEqual("bad.png: damaged", dialog.details.toPlainText())

        dialog.show_result(5, 0, [])
        self.assertTrue(dialog.failure_label.property("empty"))

    def test_tiling_only_shows_relevant_fields(self) -> None:
        page = WatermarkPage()
        self.assertFalse(page.angle_field.isVisibleTo(page))
        self.assertTrue(page.position_field.isVisibleTo(page))
        page.tiled.setChecked(True)
        self.assertTrue(page.angle_field.isVisibleTo(page))
        self.assertFalse(page.position_field.isVisibleTo(page))

    def test_core_settings_fit_without_a_scroll_area(self) -> None:
        page = WatermarkPage()
        page.resize(400, 558)
        page.show()
        self.app.processEvents()
        self.assertFalse(hasattr(page, "settings_scroll"))
        for widget in (page.text_input, page.font_size, page.opacity, page.color_button, page.position, page.margin, page.tiled, page.output_button, page.start_button):
            self.assertTrue(widget.isVisible())
        page.close()

    def test_empty_state_hides_redundant_file_controls(self) -> None:
        page = WatermarkPage()
        self.assertTrue(page.preview.empty_state.isVisibleTo(page.preview))
        self.assertTrue(page.file_actions.isHidden())
        self.assertTrue(page.file_list.isHidden())
        self.assertIsNone(page.findChild(QWidget, "statusPanel"))

    def test_invalid_output_path_disables_processing(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            source = Path(name) / "测试图片.png"
            output_file = Path(name) / "不是目录.txt"
            Image.new("RGB", (20, 20), "white").save(source)
            output_file.write_text("file", encoding="utf-8")
            page = WatermarkPage()
            page.add_files([source])
            page.output_edit.setText(str(output_file))
            self.assertFalse(page.start_button.isEnabled())
            self.assertEqual("输出路径不能是文件", page.output_error.text())

    def test_settings_restore_without_restoring_task(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            output = Path(name)
            page = WatermarkPage()
            page.text_input.setText("公司内部使用")
            page.font_size.setValue(32)
            page.opacity.setValue(89)
            page.margin.setValue(36)
            page.tiled.setChecked(True)
            page.angle.setValue(-25)
            page.spacing.setValue(120)
            page.output_edit.setText(str(output))

            restored = WatermarkPage()
            self.assertEqual("公司内部使用", restored.text_input.text())
            self.assertEqual(32, restored.font_size.value())
            self.assertEqual(89, restored.opacity.value())
            self.assertEqual(36, restored.margin.value())
            self.assertTrue(restored.tiled.isChecked())
            self.assertEqual(-25, restored.angle.value())
            self.assertEqual(120, restored.spacing.value())
            self.assertEqual(str(output), restored.output_edit.text())
            self.assertEqual([], restored.sources)

    def test_recent_watermark_text_keeps_three_used_values(self) -> None:
        page = WatermarkPage()
        for text in ("水印一", "水印二", "水印三", "水印二", "水印四"):
            page.text_input.setText(text)
            page._remember_current_text()
        self.assertTrue(page.text_input.isEditable())
        self.assertEqual(["水印四", "水印二", "水印三"], page.text_input.history())

        restored = WatermarkPage()
        self.assertEqual(["水印四", "水印二", "水印三"], restored.text_input.history())
        restored.text_input.setText("直接输入的新文字")
        self.assertEqual("直接输入的新文字", restored.text_input.text())

    def test_clicking_watermark_text_opens_recent_choices(self) -> None:
        page = WatermarkPage()
        page.text_input.set_history(["最近使用的水印"])
        page.show()
        QTest.mouseClick(page.text_input.lineEdit(), Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertTrue(page.text_input.view().isVisible())
        page.text_input.hidePopup()
        page.close()

    def test_restore_defaults_keeps_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            page = WatermarkPage()
            page.output_edit.setText(name)
            page.text_input.setText("自定义水印")
            page.font_size.setValue(88)
            page.restore_defaults()
            self.assertEqual(WatermarkPage.DEFAULT_TEXT, page.text_input.text())
            self.assertEqual(WatermarkPage.DEFAULT_FONT_SIZE, page.font_size.value())
            self.assertEqual(name, page.output_edit.text())

    def test_output_format_controls_and_settings(self) -> None:
        page = WatermarkPage()
        self.assertEqual("original", page.output_format.currentData())
        self.assertFalse(page.quality_field.isVisibleTo(page))
        page.output_format.setCurrentIndex(page.output_format.findData("jpg"))
        self.assertTrue(page.quality_field.isVisibleTo(page))
        self.assertTrue(page.jpg_notice.isVisibleTo(page))
        page.quality.setValue(88)

        restored = WatermarkPage()
        self.assertEqual("jpg", restored.output_format.currentData())
        self.assertEqual(88, restored.quality.value())

    def test_missing_previous_output_falls_back_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "watermark")
            settings.setValue("output_dir", str(Path(name) / "deleted-output"))
            settings.setValue("font_size", "damaged")
            settings.sync()
            page = WatermarkPage()
            self.assertEqual(str(Path.cwd() / "output"), page.output_edit.text())
            self.assertEqual(WatermarkPage.DEFAULT_FONT_SIZE, page.font_size.value())
            self.assertEqual("上次使用的输出目录不可用，请重新选择。", page.output_notice.text())
            self.assertFalse(page.output_notice.isHidden())

    def test_file_dialog_reopens_last_source_directory(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            source = folder / "商品图.png"
            Image.new("RGB", (20, 20), "white").save(source)
            page = WatermarkPage()
            page.add_files([source])

            restored = WatermarkPage()
            with patch.object(QFileDialog, "getOpenFileNames", return_value=([], "")) as dialog:
                restored.choose_files()
            self.assertEqual(str(folder.resolve()), dialog.call_args.args[2])

    def test_missing_source_directory_falls_back_to_user_home(self) -> None:
        settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "watermark")
        settings.setValue("source_dir", str(Path(tempfile.gettempdir()) / "missing-source-directory"))
        settings.sync()
        self.assertEqual(str(Path.home()), WatermarkPage()._source_dialog_dir())


if __name__ == "__main__":
    unittest.main()
