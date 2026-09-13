from PySide6.QtCore import QEvent, QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QComboBox, QSlider, QSpinBox, QStyle, QStyleOptionComboBox, QStyleOptionSpinBox


class AppSpinBox(QSpinBox):
    """Only change through deliberate click or keyboard input."""

    def wheelEvent(self, event) -> None:
        event.ignore()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        option = QStyleOptionSpinBox()
        self.initStyleOption(option)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        enabled = self.stepEnabled()
        controls = (
            (QStyle.SubControl.SC_SpinBoxUp, True, bool(enabled & QSpinBox.StepEnabledFlag.StepUpEnabled)),
            (QStyle.SubControl.SC_SpinBoxDown, False, bool(enabled & QSpinBox.StepEnabledFlag.StepDownEnabled)),
        )
        for control, is_plus, allowed in controls:
            rect = self.style().subControlRect(QStyle.ComplexControl.CC_SpinBox, option, control, self)
            color = QColor("#526175" if allowed and self.isEnabled() else "#B7C0CD")
            pen = QPen(color, 1.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            center = rect.center()
            painter.drawLine(QPointF(center.x() - 3.5, center.y()), QPointF(center.x() + 3.5, center.y()))
            if is_plus:
                painter.drawLine(QPointF(center.x(), center.y() - 3.5), QPointF(center.x(), center.y() + 3.5))


class AppComboBox(QComboBox):
    def wheelEvent(self, event) -> None:
        event.ignore()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        rect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, option, QStyle.SubControl.SC_ComboBoxArrow, self)
        center = rect.center()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#526175" if self.isEnabled() else "#B7C0CD"), 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPolyline(
            QPolygonF(
                [QPointF(center.x() - 4, center.y() - 2), QPointF(center.x(), center.y() + 2), QPointF(center.x() + 4, center.y() - 2)]
            )
        )


class RecentTextComboBox(AppComboBox):
    def __init__(self) -> None:
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setMaxCount(3)
        self.lineEdit().installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.lineEdit() and event.type() == QEvent.Type.MouseButtonPress and self.count():
            QTimer.singleShot(0, self.showPopup)
        return super().eventFilter(watched, event)

    def set_history(self, values: list[str]) -> None:
        current = self.currentText()
        self.blockSignals(True)
        QComboBox.clear(self)
        self.addItems(values[:3])
        self.setEditText(current)
        self.blockSignals(False)

    def history(self) -> list[str]:
        return [self.itemText(index) for index in range(self.count())]

    def text(self) -> str:
        return self.currentText()

    def setText(self, text: str) -> None:
        self.setEditText(text)

    def clear(self) -> None:
        self.lineEdit().clear()


class NoWheelSlider(QSlider):
    def wheelEvent(self, event) -> None:
        event.ignore()


# Backward-compatible names for existing callers.
NoWheelSpinBox = AppSpinBox
NoWheelComboBox = AppComboBox
