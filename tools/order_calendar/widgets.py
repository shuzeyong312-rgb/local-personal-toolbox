from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QPoint, Qt, Signal
from PySide6.QtGui import QColor, QIntValidator, QPainter, QPen, QTextCharFormat
from PySide6.QtWidgets import (
    QAbstractSpinBox, QCalendarWidget, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from app.theme import PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY
from app.icons import icon
from components.controls import AppComboBox


class NumberInput(QSpinBox):
    """Modern keyboard-first integer input without native spinner chrome."""

    def __init__(self, minimum: int = 0, maximum: int = 999999, value: int = 0) -> None:
        super().__init__()
        self.setRange(minimum, maximum)
        self.setValue(value)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lineEdit().setValidator(QIntValidator(minimum, maximum, self))

    def wheelEvent(self, event) -> None:
        event.ignore()


class ClickLineEdit(QLineEdit):
    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        self.clicked.emit()


class PickerCalendar(QCalendarWidget):
    def __init__(self) -> None:
        super().__init__()
        weekend = QTextCharFormat()
        weekend.setForeground(QColor(TEXT_SECONDARY))
        self.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend)

    def paintCell(self, painter: QPainter, rect, value: QDate) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        current_month = value.month() == self.monthShown()
        selected = value == self.selectedDate()
        today = value == QDate.currentDate()
        cell = rect.adjusted(4, 2, -4, -2)
        if selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(PRIMARY))
            painter.drawRoundedRect(cell, 6, 6)
        elif today:
            painter.setPen(QPen(QColor(PRIMARY), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(cell, 6, 6)
        color = "#FFFFFF" if selected else TEXT_PRIMARY if current_month else "#A1AAB8"
        painter.setPen(QColor(color))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(value.day()))
        painter.restore()


class DatePopover(QFrame):
    accepted = Signal(QDate)

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("datePopover")
        self.setFixedSize(310, 330)
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 12)
        root.setSpacing(10)
        header = QHBoxLayout()
        previous = QPushButton("‹", objectName="iconButton")
        following = QPushButton("›", objectName="iconButton")
        self.month = QLabel(objectName="datePickerMonth")
        self.month.setAlignment(Qt.AlignmentFlag.AlignCenter)
        previous.clicked.connect(self._previous)
        following.clicked.connect(self._following)
        header.addWidget(previous)
        header.addWidget(self.month, 1)
        header.addWidget(following)
        root.addLayout(header)
        self.calendar = PickerCalendar()
        self.calendar.setObjectName("datePickerCalendar")
        self.calendar.setNavigationBarVisible(False)
        self.calendar.setGridVisible(False)
        self.calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.calendar.currentPageChanged.connect(self._update_month)
        self.calendar.activated.connect(self._accept)
        root.addWidget(self.calendar, 1)
        footer = QHBoxLayout()
        today = QPushButton("今天", objectName="linkButton")
        confirm = QPushButton("确定", objectName="primary")
        today.clicked.connect(self._today)
        confirm.clicked.connect(lambda: self._accept(self.calendar.selectedDate()))
        footer.addWidget(today)
        footer.addStretch()
        footer.addWidget(confirm)
        root.addLayout(footer)
        self._update_month()

    def open_for(self, anchor: QWidget, value: QDate) -> None:
        self.calendar.setSelectedDate(value)
        self.calendar.setCurrentPage(value.year(), value.month())
        position = anchor.mapToGlobal(QPoint(0, anchor.height() + 6))
        screen = anchor.screen().availableGeometry()
        x = min(position.x(), screen.right() - self.width())
        y = position.y() if position.y() + self.height() <= screen.bottom() else anchor.mapToGlobal(QPoint(0, 0)).y() - self.height() - 6
        self.move(max(screen.left(), x), max(screen.top(), y))
        self.show()
        self.raise_()

    def _previous(self) -> None:
        self.calendar.showPreviousMonth()

    def _following(self) -> None:
        self.calendar.showNextMonth()

    def _today(self) -> None:
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.showToday()

    def _accept(self, value: QDate) -> None:
        self.accepted.emit(value)
        self.hide()

    def _update_month(self, *_args) -> None:
        self.month.setText(f"{self.calendar.yearShown()}年{self.calendar.monthShown()}月")


class DateInput(QWidget):
    dateChanged = Signal(QDate)

    def __init__(self, value: QDate | None = None) -> None:
        super().__init__()
        self._date = value or QDate.currentDate()
        self._valid = True
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.input = ClickLineEdit()
        self.input.setObjectName("dateInput")
        self.input.setPlaceholderText("YYYY/MM/DD")
        self.button = QPushButton(objectName="dateButton")
        self.button.setIcon(icon("calendar", TEXT_SECONDARY, 16))
        self.button.setToolTip("选择日期")
        layout.addWidget(self.input, 1)
        layout.addWidget(self.button)
        self.popover = DatePopover(self)
        self.popover.accepted.connect(self.setDate)
        self.input.clicked.connect(self.open_popup)
        self.button.clicked.connect(self.open_popup)
        self.input.editingFinished.connect(self._parse)
        self.setDate(self._date, emit=False)

    def date(self) -> QDate:
        return self._date

    def is_valid(self) -> bool:
        return self._valid

    def setDate(self, value: QDate, emit: bool = True) -> None:
        if not value.isValid():
            return
        changed = value != self._date
        self._date = value
        self._valid = True
        self.input.setProperty("error", False)
        self.input.style().unpolish(self.input)
        self.input.style().polish(self.input)
        self.input.setText(value.toString("yyyy/MM/dd"))
        if emit and changed:
            self.dateChanged.emit(value)

    def open_popup(self) -> None:
        self.popover.open_for(self, self._date)

    def _parse(self) -> None:
        text = self.input.text().strip().replace("-", "/")
        value = QDate.fromString(text, "yyyy/MM/dd")
        self._valid = value.isValid()
        self.input.setProperty("error", not self._valid)
        self.input.style().unpolish(self.input)
        self.input.style().polish(self.input)
        if self._valid:
            self.setDate(value)


class StageRuleCard(QFrame):
    changed = Signal()
    remove_requested = Signal(object)

    def __init__(self, stage: dict, index: int = 0) -> None:
        super().__init__(objectName="stageCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.index = index
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)
        heading = QHBoxLayout()
        self.title = QLabel(objectName="stageTitle")
        remove = QPushButton("删除", objectName="dangerLink")
        remove.clicked.connect(lambda: self.remove_requested.emit(self))
        heading.addWidget(self.title)
        heading.addStretch()
        heading.addWidget(remove)
        root.addLayout(heading)
        fields = QGridLayout()
        fields.setHorizontalSpacing(14)
        fields.setVerticalSpacing(6)
        self.kind = AppComboBox()
        self.kind.addItem("固定次数", "fixed_count")
        self.kind.addItem("累计数量", "until_total")
        self.kind.addItem("持续执行", "continuous")
        self.kind.setCurrentIndex(max(0, self.kind.findData(stage["type"])))
        self.value_label = QLabel(objectName="fieldLabel")
        self.value_input = NumberInput(1, 999999, int(stage.get("count", stage.get("until_total", 1))))
        self.frequency = NumberInput(1, 3650, int(stage["frequency_days"]))
        self.target = NumberInput(1, 999999, int(stage["target_quantity"]))
        fields.addWidget(QLabel("阶段类型", objectName="fieldLabel"), 0, 0)
        fields.addWidget(self.value_label, 0, 1)
        fields.addWidget(QLabel("频率", objectName="fieldLabel"), 0, 2)
        fields.addWidget(QLabel("每次目标", objectName="fieldLabel"), 0, 3)
        fields.addWidget(self.kind, 1, 0)
        fields.addWidget(self.value_input, 1, 1)
        frequency_row = QHBoxLayout()
        frequency_row.setSpacing(7)
        frequency_row.addWidget(QLabel("每", objectName="fieldValue"))
        frequency_row.addWidget(self.frequency, 1)
        frequency_row.addWidget(QLabel("天一次", objectName="fieldValue"))
        fields.addLayout(frequency_row, 1, 2)
        target_row = QHBoxLayout()
        target_row.setSpacing(7)
        target_row.addWidget(self.target, 1)
        target_row.addWidget(QLabel("单", objectName="fieldValue"))
        fields.addLayout(target_row, 1, 3)
        fields.setColumnStretch(0, 3)
        fields.setColumnStretch(1, 2)
        fields.setColumnStretch(2, 3)
        fields.setColumnStretch(3, 2)
        root.addLayout(fields)
        self.error = QLabel(objectName="fieldError")
        self.error.hide()
        root.addWidget(self.error)
        self.kind.currentIndexChanged.connect(self._kind_changed)
        self.kind.currentIndexChanged.connect(self.changed)
        self.value_input.valueChanged.connect(self.changed)
        self.frequency.valueChanged.connect(self.changed)
        self.target.valueChanged.connect(self.changed)
        self._kind_changed()
        self.set_index(index)

    def set_index(self, index: int) -> None:
        self.index = index
        self.title.setText(f"阶段 {index + 1}")

    def _kind_changed(self, *_args) -> None:
        kind = self.kind.currentData()
        self.value_label.setText("执行次数" if kind == "fixed_count" else "计划累计达到" if kind == "until_total" else "")
        self.value_label.setVisible(kind != "continuous")
        self.value_input.setVisible(kind != "continuous")

    def value(self) -> dict:
        stage = {"type": self.kind.currentData(), "frequency_days": self.frequency.value(), "target_quantity": self.target.value()}
        if stage["type"] == "fixed_count":
            stage["count"] = self.value_input.value()
        elif stage["type"] == "until_total":
            stage["until_total"] = self.value_input.value()
        return stage

    def set_error(self, text: str = "") -> None:
        self.error.setText(text)
        self.error.setVisible(bool(text))


class StageRuleEditor(QWidget):
    changed = Signal()

    def __init__(self, stages: list[dict]) -> None:
        super().__init__()
        self.cards: list[StageRuleCard] = []
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(10)
        root.addLayout(self.cards_layout)
        footer = QHBoxLayout()
        self.add_button = QPushButton("+ 添加阶段")
        self.add_button.clicked.connect(self.add_stage)
        self.hint = QLabel("持续执行阶段必须作为最后一个阶段。", objectName="helperText")
        footer.addWidget(self.add_button)
        footer.addWidget(self.hint)
        footer.addStretch()
        root.addLayout(footer)
        for stage in stages:
            self.add_stage(stage)

    def add_stage(self, stage: dict | None = None) -> None:
        if self.cards and self.cards[-1].kind.currentData() == "continuous":
            return
        card = StageRuleCard(stage or {"type": "fixed_count", "count": 1, "frequency_days": 1, "target_quantity": 1}, len(self.cards))
        card.changed.connect(lambda _=None, item=card: self._card_changed(item))
        card.remove_requested.connect(self.remove_stage)
        self.cards.append(card)
        self.cards_layout.addWidget(card)
        self._changed()

    def remove_stage(self, card: StageRuleCard) -> None:
        if len(self.cards) == 1:
            card.set_error("至少保留一个阶段。")
            return
        self.cards.remove(card)
        card.deleteLater()
        self._renumber()
        self._changed()

    def _renumber(self) -> None:
        for index, card in enumerate(self.cards):
            card.set_index(index)

    def _card_changed(self, card: StageRuleCard) -> None:
        if card.kind.currentData() == "continuous" and card is not self.cards[-1]:
            if any(item is not card and item.kind.currentData() == "continuous" for item in self.cards):
                card.kind.blockSignals(True)
                card.kind.setCurrentIndex(card.kind.findData("fixed_count"))
                card.kind.blockSignals(False)
                card._kind_changed()
                card.set_error("已有持续执行阶段，请先调整最后一个阶段。")
            else:
                self.cards.remove(card)
                self.cards.append(card)
                self.cards_layout.removeWidget(card)
                self.cards_layout.addWidget(card)
                self._renumber()
        self._changed()

    def _changed(self, *_args) -> None:
        continuous = [index for index, card in enumerate(self.cards) if card.kind.currentData() == "continuous"]
        invalid = bool(continuous and continuous[-1] != len(self.cards) - 1)
        self.add_button.setEnabled(not continuous)
        self.hint.setProperty("error", invalid)
        self.hint.setText("持续执行阶段必须作为最后一个阶段。" if continuous else "按计划累计数量推进阶段。")
        self.changed.emit()

    def values(self) -> list[dict]:
        return [card.value() for card in self.cards]

    def validate(self, initial: int) -> bool:
        valid = bool(self.cards)
        running = initial
        for index, card in enumerate(self.cards):
            card.set_error()
            stage = card.value()
            if stage["type"] == "continuous" and index != len(self.cards) - 1:
                card.set_error("持续执行阶段必须作为最后一个阶段。")
                valid = False
            elif stage["type"] == "until_total" and stage["until_total"] <= running:
                card.set_error(f"累计数量必须大于当前阶段起始累计数量 {running}。")
                valid = False
            if stage["type"] == "fixed_count":
                running += stage["count"] * stage["target_quantity"]
            elif stage["type"] == "until_total":
                running = stage["until_total"]
        return valid


class PlanPreview(QWidget):
    def __init__(self) -> None:
        super().__init__(objectName="planPreview")
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(14, 12, 14, 12)
        self.layout.setHorizontalSpacing(22)
        self.layout.setVerticalSpacing(8)

    def show_empty(self) -> None:
        self._clear()
        title = QLabel("请先填写商品信息和阶段规则", objectName="emptyTitle")
        hint = QLabel("完成后将在这里预览未来计划日期。", objectName="emptyHint")
        self.layout.addWidget(title, 0, 0, 1, 2)
        self.layout.addWidget(hint, 1, 0, 1, 2)

    def show_tasks(self, tasks: list[dict], model: str) -> None:
        self._clear()
        for index, task in enumerate(tasks):
            row, column = divmod(index, 2)
            item = QLabel(f"{task['date'][5:].replace('-', '/')}   {model} ×{task['target_quantity']}", objectName="previewItem")
            self.layout.addWidget(item, row, column)

    def _clear(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()


class EmptyState(QWidget):
    action_requested = Signal()

    def __init__(self) -> None:
        super().__init__(objectName="emptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 28, 18, 28)
        layout.setSpacing(7)
        layout.addStretch()
        self.title = QLabel(objectName="emptyTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint = QLabel(objectName="emptyHint")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setWordWrap(True)
        self.action = QPushButton("新增计划", objectName="primary")
        self.action.clicked.connect(self.action_requested)
        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        layout.addWidget(self.action, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def configure(self, title: str, hint: str = "", action: bool = False) -> None:
        self.title.setText(title)
        self.hint.setText(hint)
        self.hint.setVisible(bool(hint))
        self.action.setVisible(action)
