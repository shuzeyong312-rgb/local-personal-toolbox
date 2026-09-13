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
from PySide6.QtWidgets import QApplication, QFileDialog, QPlainTextEdit, QPushButton, QSplitter

from app.main_window import MainWindow
from app.theme import STYLE
from components.controls import AppComboBox, AppSpinBox
from components.dialogs import ResultDialog
from tools.watermark.page import WatermarkPage


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

    def test_result_dialog_exposes_failures_and_actions(self) -> None:
        dialog = ResultDialog(2, 1, Path("output"), ["bad.png: damaged"])
        details = dialog.findChild(QPlainTextEdit, "failureDetails")
        self.assertIsNotNone(details)
        self.assertEqual("bad.png: damaged", details.toPlainText())
        labels = [button.text() for button in dialog.findChildren(QPushButton)]
        self.assertIn("关闭", labels)
        self.assertIn("打开文件夹", labels)

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
        self.assertTrue(page.status_panel.isHidden())

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
