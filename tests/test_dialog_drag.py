import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from components.dialogs import BaseDialog


class DialogDragTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_dragging_title_moves_frameless_dialog(self) -> None:
        dialog = BaseDialog("测试弹窗")
        dialog.move(100, 100)
        dialog.show()
        self.app.processEvents()
        origin = dialog.pos()

        press_global = QPointF(origin.x() + 40, origin.y() + 24)
        press = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(40, 24),
            press_global,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.assertTrue(dialog.eventFilter(dialog.title_label, press))

        delta = QPoint(70, 45)
        move = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(110, 69),
            QPointF(press_global.x() + delta.x(), press_global.y() + delta.y()),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.assertTrue(dialog.eventFilter(dialog.title_label, move))
        self.assertEqual(origin + delta, dialog.pos())

        release = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            QPointF(110, 69),
            QPointF(press_global.x() + delta.x(), press_global.y() + delta.y()),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.assertTrue(dialog.eventFilter(dialog.title_label, release))
        self.assertIsNone(dialog._drag_offset)
        dialog.close()


if __name__ == "__main__":
    unittest.main()
