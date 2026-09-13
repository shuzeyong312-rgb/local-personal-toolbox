import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from tools.watermark.page import WatermarkPage


class UiStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

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


if __name__ == "__main__":
    unittest.main()
