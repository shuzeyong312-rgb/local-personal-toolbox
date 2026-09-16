from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QDate, QEvent, QPoint, QRect, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QTextCharFormat
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCalendarWidget, QFrame, QGridLayout, QHBoxLayout, QLabel, QLayout,
    QLineEdit, QPushButton, QScrollArea, QSizePolicy, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.theme import BORDER, DANGER, PRIMARY, SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY, WARNING
from components.dialogs import BaseDialog
from components.controls import AppComboBox
from services.order_calendar import DATA_VERSION, PLATFORMS, CalendarStore, OrderCalendar, parse_date, platform_name, review_status, task_status
from tools.order_calendar.widgets import DateInput, EmptyState, NumberInput, PlanPreview, StageRuleEditor


def show_message(parent: QWidget, title: str, text: str, confirm: bool = False) -> bool:
    dialog = BaseDialog(title, parent)
    message = QLabel(text, objectName="statusText")
    message.setWordWrap(True)
    dialog.layout.addWidget(message)
    actions = QHBoxLayout()
    actions.addStretch()
    if confirm:
        cancel = QPushButton("取消")
        cancel.clicked.connect(dialog.reject)
        actions.addWidget(cancel)
    accept = QPushButton("确定", objectName="primary")
    accept.clicked.connect(dialog.accept)
    actions.addWidget(accept)
    dialog.layout.addLayout(actions)
    return dialog.exec() == dialog.DialogCode.Accepted


def as_date(value: QDate) -> date:
    return date(value.year(), value.month(), value.day())


def as_qdate(value: date) -> QDate:
    return QDate(value.year, value.month, value.day)


def platform_combo(value: str = "jd", include_all: bool = False, include_unknown: bool = False) -> AppComboBox:
    combo = AppComboBox()
    if include_all:
        combo.addItem("全部平台", "all")
    if include_unknown:
        combo.addItem("未设置平台", "unknown")
    for code, label in PLATFORMS:
        combo.addItem(label, code)
    index = combo.findData(value)
    combo.setCurrentIndex(index if index >= 0 else 0)
    return combo


class TaskCalendar(QCalendarWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("taskCalendar")
        self.tasks: dict[str, list[dict]] = {}
        self._hovered_date = QDate()
        self._keyboard_focus = False
        self.setNavigationBarVisible(False)
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.setSelectionMode(QCalendarWidget.SelectionMode.SingleSelection)
        self._calendar_view = self.findChild(QAbstractItemView)
        self._calendar_view.installEventFilter(self)
        self._calendar_view.viewport().installEventFilter(self)
        self._calendar_view.viewport().setMouseTracking(True)
        weekend = QTextCharFormat()
        weekend.setForeground(QColor(TEXT_SECONDARY))
        self.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend)

    def paintCell(self, painter: QPainter, rect: QRect, value: QDate) -> None:
        day = as_date(value)
        items = self.tasks.get(day.isoformat(), [])
        current_month = value.month() == self.monthShown()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(BORDER)))
        selected = value == self.selectedDate()
        hovered = value == self._hovered_date and not selected
        painter.setBrush(QColor("#F8FAFC" if hovered or not current_month else "#FFFFFF"))
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 7, 7)
        if day == date.today() and not selected:
            painter.setPen(QPen(QColor(PRIMARY), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 7, 7)
        if selected:
            painter.setBrush(QColor("#F0F5FF"))
            painter.setPen(QPen(QColor("#B8CCF4")))
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 7, 7)
            if self._keyboard_focus:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(59, 130, 246, 31), 2))
                painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 8, 8)
            font = painter.font(); font.setWeight(QFont.Weight.Medium); painter.setFont(font)
        painter.setPen(QColor("#1F2937" if selected else TEXT_PRIMARY if current_month else "#A1AAB8"))
        painter.drawText(rect.adjusted(9, 6, -7, -5), Qt.AlignmentFlag.AlignTop, str(value.day()))
        if items and current_month:
            statuses = [task_status(item["target_quantity"], item["actual_quantity"], day) for item in items]
            marker = "!" if "missed" in statuses else "✓" if set(statuses) == {"completed"} else "●"
            painter.setPen(QColor(DANGER if marker == "!" else SUCCESS if marker == "✓" else PRIMARY))
            painter.drawText(rect.adjusted(9, 8, -8, -8), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
                             f"{marker} {len(items)}")
        painter.restore()

    def eventFilter(self, watched, event) -> bool:
        if watched is self._calendar_view:
            if event.type() == QEvent.Type.FocusIn:
                self._keyboard_focus = event.reason() in (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason)
                self.updateCell(self.selectedDate())
            elif event.type() == QEvent.Type.FocusOut:
                self._keyboard_focus = False
                self.updateCell(self.selectedDate())
        elif watched is self._calendar_view.viewport():
            if event.type() == QEvent.Type.MouseMove:
                hovered = self._date_at(event.position().toPoint())
                if hovered != self._hovered_date:
                    previous, self._hovered_date = self._hovered_date, hovered
                    if previous.isValid(): self.updateCell(previous)
                    if hovered.isValid(): self.updateCell(hovered)
            elif event.type() == QEvent.Type.Leave and self._hovered_date.isValid():
                previous, self._hovered_date = self._hovered_date, QDate()
                self.updateCell(previous)
        return super().eventFilter(watched, event)

    def _date_at(self, position: QPoint) -> QDate:
        index = self._calendar_view.indexAt(position)
        if not index.isValid() or index.row() == 0:
            return QDate()
        first = QDate(self.yearShown(), self.monthShown(), 1)
        offset = (first.dayOfWeek() - self.firstDayOfWeek().value + 7) % 7
        return first.addDays(-offset + (index.row() - 1) * 7 + index.column())


class PlanDialog(BaseDialog):
    def __init__(self, calendar: OrderCalendar, plan: dict | None = None, parent=None) -> None:
        super().__init__("编辑计划" if plan else "新增商品计划", parent)
        self.calendar = calendar
        self.plan = plan
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "order_calendar")
        self.setMinimumWidth(720)
        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            self.setMaximumHeight(max(620, screen.availableGeometry().height() - 60))
            self.resize(760, min(820, self.maximumHeight()))
        body_scroll = QScrollArea(objectName="planDialogScroll")
        body_scroll.setWidgetResizable(True)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(2, 0, 8, 0)
        body_layout.setSpacing(14)
        body_layout.addWidget(self._section("商品信息"))
        form = QGridLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)
        selected_platform = plan.get("platform", "unknown") if plan else self.settings.value("last_platform", "jd", type=str)
        self.platform = platform_combo(selected_platform, include_unknown=selected_platform == "unknown")
        self.custom_platform = QLineEdit(plan.get("custom_platform_name", "") if plan else "")
        self.custom_platform.setPlaceholderText("例如：小红书")
        self.model = QLineEdit(plan.get("model", "") if plan else "")
        self.start_date = DateInput(as_qdate(parse_date(plan["start_date"])) if plan else QDate.currentDate())
        self.initial = NumberInput(0, 999999, int(plan.get("initial_completed_quantity", 0)) if plan else 0)
        self.note = QLineEdit(plan.get("note", "") if plan else "")
        self.errors: dict[str, QLabel] = {}
        fields = (("平台", self.platform), ("平台名称", self.custom_platform), ("型号", self.model), ("开始日期", self.start_date),
                  ("初始已出单数量", self.initial), ("备注", self.note))
        for row, (label, widget) in enumerate(fields):
            field, error = self._field(label, widget)
            self.errors[label] = error
            form.addWidget(field, row, 0)
        body_layout.addLayout(form)
        body_layout.addWidget(self._section("阶段规则"))
        stages = plan.get("stages", []) if plan else [
            {"type": "fixed_count", "count": 3, "frequency_days": 1, "target_quantity": 1},
            {"type": "until_total", "until_total": 10, "frequency_days": 2, "target_quantity": 1},
            {"type": "continuous", "frequency_days": 7, "target_quantity": 1},
        ]
        self.stages = StageRuleEditor(stages)
        body_layout.addWidget(self.stages)
        body_layout.addWidget(self._section("计划预览", "未来 10 次计划日期"))
        self.preview = PlanPreview()
        body_layout.addWidget(self.preview)
        body_layout.addStretch()
        body_scroll.setWidget(body)
        self.layout.addWidget(body_scroll, 1)
        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("取消")
        save = QPushButton("保存计划", objectName="primary")
        cancel.setAutoDefault(False)
        save.setAutoDefault(False)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save)
        actions.addWidget(cancel)
        actions.addWidget(save)
        self.layout.addLayout(actions)
        for signal in (self.platform.currentIndexChanged, self.custom_platform.textChanged, self.model.textChanged, self.start_date.dateChanged, self.initial.valueChanged):
            signal.connect(self.refresh_preview)
        self.platform.currentIndexChanged.connect(self._platform_changed)
        self.stages.changed.connect(self.refresh_preview)
        self._platform_changed()
        self.refresh_preview()

    @staticmethod
    def _section(title: str, subtitle: str = "") -> QWidget:
        section = QWidget(objectName="dialogSection")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)
        row = QHBoxLayout()
        row.addWidget(QLabel(title, objectName="sectionTitle"))
        if subtitle:
            row.addWidget(QLabel(subtitle, objectName="sectionHint"))
        row.addStretch()
        layout.addLayout(row)
        line = QFrame(objectName="sectionDivider")
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        return section

    @staticmethod
    def _field(label: str, widget: QWidget) -> tuple[QWidget, QLabel]:
        field = QWidget()
        layout = QVBoxLayout(field)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(QLabel(label, objectName="fieldLabel"))
        layout.addWidget(widget)
        error = QLabel(objectName="fieldError")
        error.hide()
        layout.addWidget(error)
        return field, error

    def _platform_changed(self, *_args) -> None:
        visible = self.platform.currentData() == "other"
        self.custom_platform.parentWidget().setVisible(visible)

    def _set_error(self, field: str, text: str = "") -> None:
        label = self.errors[field]
        label.setText(text)
        label.setVisible(bool(text))

    def value(self) -> dict:
        return {
            "id": self.plan.get("id") if self.plan else None,
            "platform": self.platform.currentData(), "custom_platform_name": self.custom_platform.text().strip(),
            "model": self.model.text().strip(),
            "start_date": as_date(self.start_date.date()).isoformat(), "initial_completed_quantity": self.initial.value(),
            "status": self.plan.get("status", "active") if self.plan else "active", "stages": self.stages.values(), "note": self.note.text().strip(),
        }

    def refresh_preview(self, *_args) -> None:
        try:
            plan = self.value()
            self.calendar._validate_plan(plan)
            if not self.start_date.is_valid() or not self.stages.validate(self.initial.value()):
                raise ValueError
            self.preview.show_tasks(self.calendar.preview(plan), plan["model"])
        except (ValueError, KeyError):
            self.preview.show_empty()

    def _save(self) -> None:
        for field in self.errors:
            self._set_error(field)
        valid = True
        if self.platform.currentData() == "unknown":
            self._set_error("平台", "请选择平台。")
            valid = False
        if self.platform.currentData() == "other" and not self.custom_platform.text().strip():
            self._set_error("平台名称", "请输入平台名称。")
            valid = False
        if not self.model.text().strip():
            self._set_error("型号", "请输入型号。")
            valid = False
        if not self.start_date.is_valid():
            self._set_error("开始日期", "请输入有效日期，例如 2026/09/16。")
            valid = False
        if not self.stages.validate(self.initial.value()):
            valid = False
        if not valid:
            return
        try:
            value = self.value()
            if not self.plan:
                duplicate = self.calendar.active_plan(value["platform"], value["model"])
                if duplicate and not show_message(self, "计划已存在", f"{platform_name(value)}平台已经存在 {value['model']} 的进行中计划。\n是否仍继续创建？", confirm=True):
                    return
            if self.plan:
                self.calendar.update_plan(self.plan["id"], value)
            else:
                self.calendar.add_plan(value)
            self.settings.setValue("last_platform", value["platform"])
            self.settings.sync()
        except ValueError as exc:
            show_message(self, "无法保存", str(exc))
            return
        self.accept()


class TaskDialog(BaseDialog):
    def __init__(self, calendar: OrderCalendar, day: date, task: dict | None = None, parent=None) -> None:
        super().__init__("编辑当天任务" if task else "添加临时任务", parent)
        self.calendar, self.day, self.task = calendar, day, task
        selected_platform = task.get("platform", "jd") if task else "jd"
        self.platform = platform_combo(selected_platform, include_unknown=selected_platform == "unknown")
        self.custom_platform = QLineEdit(task.get("custom_platform_name", "") if task else "")
        self.custom_platform.setPlaceholderText("例如：小红书")
        self.model = QLineEdit(task.get("model", "") if task else "")
        self.target = NumberInput(1, 999999, task.get("target_quantity", 1) if task else 1)
        self.actual = NumberInput(0, 999999, task.get("actual_quantity", 0) if task else 0)
        self.reviewed = NumberInput(0, 999999, task.get("reviewed_quantity", 0) if task else 0)
        self.note = QLineEdit(task.get("note", "") if task else "")
        grid = QGridLayout()
        fields = (("平台", self.platform), ("平台名称", self.custom_platform), ("型号", self.model), ("计划数量", self.target),
                  ("实际数量", self.actual), ("已评价数量", self.reviewed), ("备注", self.note))
        for row, (label, widget) in enumerate(fields):
            field_label = QLabel(label, objectName="fieldLabel")
            if label == "平台名称":
                self.custom_platform_label = field_label
            grid.addWidget(field_label, row, 0); grid.addWidget(widget, row, 1)
        self.platform.setEnabled(task is None or not task.get("plan_id"))
        self.model.setEnabled(task is None or not task.get("plan_id"))
        self.platform.currentIndexChanged.connect(self._platform_changed)
        self._platform_changed()
        self.layout.addLayout(grid)
        actions = QHBoxLayout(); actions.addStretch()
        cancel = QPushButton("取消"); save = QPushButton("保存", objectName="primary")
        cancel.clicked.connect(self.reject); save.clicked.connect(self._save)
        actions.addWidget(cancel); actions.addWidget(save); self.layout.addLayout(actions)

    def _save(self) -> None:
        if self.platform.currentData() == "unknown" or not self.model.text().strip():
            show_message(self, "无法保存", "请选择平台并填写型号。"); return
        if self.platform.currentData() == "other" and not self.custom_platform.text().strip():
            show_message(self, "无法保存", "请输入平台名称。"); return
        self.calendar.upsert_record(
            self.task.get("plan_id") if self.task else None, self.day,
            record_id=self.task.get("id") if self.task else None,
            source=self.task.get("source", "schedule") if self.task else "manual",
            platform=self.platform.currentData(), custom_platform_name=self.custom_platform.text().strip(), model=self.model.text().strip(),
            target_quantity=self.target.value(), actual_quantity=self.actual.value(),
            reviewed_quantity=self.reviewed.value(), note=self.note.text().strip(),
        )
        self.accept()

    def _platform_changed(self, *_args) -> None:
        visible = self.platform.currentData() == "other"
        self.custom_platform_label.setVisible(visible)
        self.custom_platform.setVisible(visible)


class PlanManagerDialog(BaseDialog):
    changed = Signal()

    def __init__(self, calendar: OrderCalendar, parent=None) -> None:
        super().__init__("计划管理", parent)
        self.calendar = calendar
        self.setMinimumWidth(760)
        self.table = QTableWidget(0, 6, objectName="previewTable")
        self.table.setHorizontalHeaderLabels(["平台", "型号", "当前阶段", "累计出单", "下一计划日", "状态"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().hide(); self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.layout.addWidget(self.table)
        actions = QHBoxLayout()
        for label, handler in (("编辑", self.edit), ("暂停/恢复", self.toggle), ("结束", self.end), ("删除", self.delete)):
            button = QPushButton(label, objectName="ghost" if label == "删除" else "")
            button.clicked.connect(handler); actions.addWidget(button)
        actions.addStretch(); close = QPushButton("关闭", objectName="primary"); close.clicked.connect(self.accept); actions.addWidget(close)
        self.layout.addLayout(actions); self.refresh()

    def selected(self) -> dict | None:
        row = self.table.currentRow()
        return self._displayed_plans[row] if 0 <= row < len(self._displayed_plans) else None

    def refresh(self) -> None:
        self._displayed_plans = sorted(self.calendar.plans, key=lambda item: (platform_name(item), item["model"].casefold()))
        self.table.setRowCount(len(self._displayed_plans))
        future_end = date.today() + timedelta(days=365)
        for row, plan in enumerate(self._displayed_plans):
            actual = int(plan.get("initial_completed_quantity", 0)) + sum(int(r.get("actual_quantity", 0)) for r in self.calendar.records if r.get("plan_id") == plan["id"])
            planned = int(plan.get("initial_completed_quantity", 0)) + sum(
                task["target_quantity"] for task in self.calendar.scheduled(plan, parse_date(plan["start_date"]), date.today())
            )
            remaining = int(plan.get("schedule_completed_occurrences", 0))
            running = int(plan.get("initial_completed_quantity", 0))
            for stage in plan["stages"]:
                target = int(stage["target_quantity"])
                available = (int(stage["count"]) if stage["type"] == "fixed_count" else
                             max(0, -(-(int(stage["until_total"]) - running) // target))
                             if stage["type"] == "until_total" else remaining)
                used = min(remaining, available)
                planned += used * target
                running += used * target
                remaining -= used
                if not remaining:
                    break
            future = self.calendar.scheduled(plan, date.today(), future_end)
            next_day = future[0]["date"] if future else "—"
            values = (platform_name(plan), plan["model"], self._stage(plan, planned), str(actual), next_day,
                      {"active": "进行中", "paused": "已暂停", "ended": "已结束"}.get(plan["status"], plan["status"]))
            for column, value in enumerate(values): self.table.setItem(row, column, QTableWidgetItem(value))

    @staticmethod
    def _stage(plan: dict, planned: int) -> str:
        running = int(plan.get("initial_completed_quantity", 0))
        for stage in plan["stages"]:
            if stage["type"] == "fixed_count":
                running += stage["count"] * stage["target_quantity"]
                if planned < running: return f"前 {stage['count']} 次"
            if stage["type"] == "until_total" and planned < stage["until_total"]: return f"每 {stage['frequency_days']} 天"
            if stage["type"] == "continuous": return f"每 {stage['frequency_days']} 天"
        return "—"

    def edit(self) -> None:
        plan = self.selected()
        if plan and PlanDialog(self.calendar, plan, self).exec(): self.refresh(); self.changed.emit()

    def toggle(self) -> None:
        plan = self.selected()
        if plan and plan["status"] != "ended":
            self.calendar.update_plan(plan["id"], {"status": "active" if plan["status"] == "paused" else "paused"})
            self.refresh(); self.changed.emit()

    def end(self) -> None:
        plan = self.selected()
        if plan: self.calendar.update_plan(plan["id"], {"status": "ended"}); self.refresh(); self.changed.emit()

    def delete(self) -> None:
        plan = self.selected()
        if plan and show_message(self, "删除计划", f"确定彻底删除 {platform_name(plan)} · {plan['model']} 及其记录？", confirm=True):
            self.calendar.delete_plan(plan["id"]); self.refresh(); self.changed.emit()


class OrderCalendarPage(QWidget):
    def __init__(self, data_path: Path | str = Path("data/order_calendar.json")) -> None:
        super().__init__()
        self.error = ""
        try:
            self.calendar_data = OrderCalendar(CalendarStore(data_path))
        except ValueError as exc:
            self.error = str(exc)
            self.calendar_data = OrderCalendar.__new__(OrderCalendar)
            self.calendar_data.store = CalendarStore(data_path)
            self.calendar_data.data = {"version": DATA_VERSION, "plans": [], "records": []}
        self.selected_day = date.today()
        self._build_ui()
        self.refresh()
        if self.error:
            self.notice.setText(self.error); self.notice.show()
        elif self.calendar_data.store.recovery_message:
            self.notice.setText(self.calendar_data.store.recovery_message); self.notice.show()

    def _build_ui(self) -> None:
        self.setObjectName("page")
        page_layout = QVBoxLayout(self); page_layout.setContentsMargins(0, 0, 0, 0)
        page_scroll = QScrollArea(objectName="orderCalendarPageScroll")
        page_scroll.setWidgetResizable(True)
        page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(objectName="orderCalendarContent")
        root = QVBoxLayout(content); root.setContentsMargins(28, 14, 28, 20); root.setSpacing(10)
        page_scroll.setWidget(content); page_layout.addWidget(page_scroll)
        header = QHBoxLayout(); titles = QVBoxLayout(); titles.setSpacing(2)
        titles.addWidget(QLabel("出单日历", objectName="pageTitle")); titles.addWidget(QLabel("今天该出哪些商品，之前还有哪些单没评价。", objectName="pageSubtitle"))
        header.addLayout(titles); header.addStretch()
        header.addWidget(QLabel("平台", objectName="fieldLabel"))
        self.platform_filter = platform_combo("all", include_all=True)
        self.platform_filter.setMinimumWidth(120)
        self.platform_filter.currentIndexChanged.connect(self.refresh)
        header.addWidget(self.platform_filter)
        self.month_label = QLabel(objectName="cardTitle")
        previous = QPushButton("‹"); following = QPushButton("›"); today = QPushButton("今天")
        plans = QPushButton("计划管理"); add = QPushButton("+ 新增计划", objectName="primary")
        previous.clicked.connect(lambda: self._move_month(-1)); following.clicked.connect(lambda: self._move_month(1)); today.clicked.connect(self.go_today)
        plans.clicked.connect(self.manage_plans); add.clicked.connect(self.add_plan)
        for widget in (previous, self.month_label, following, today, plans, add): header.addWidget(widget)
        root.addLayout(header)
        self.notice = QLabel(objectName="warningText"); self.notice.hide(); root.addWidget(self.notice)
        stats = QHBoxLayout(); self.stats = []
        for title in ("今日任务", "今日已完成", "历史未完成", "待评价"):
            card = QWidget(objectName="card"); layout = QVBoxLayout(card); layout.setContentsMargins(14, 10, 14, 10)
            label = QLabel("0", objectName="statValue"); layout.addWidget(QLabel(title, objectName="statLabel")); layout.addWidget(label)
            stats.addWidget(card); self.stats.append(label)
        root.addLayout(stats)
        body_widget = QWidget(objectName="calendarAndDetail")
        body_widget.setMinimumHeight(390)
        body_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        body = QHBoxLayout(body_widget); body.setContentsMargins(0, 0, 0, 0); body.setSpacing(14)
        calendar_card = QWidget(objectName="card"); cal_layout = QVBoxLayout(calendar_card); cal_layout.setContentsMargins(12, 12, 12, 12)
        self.calendar = TaskCalendar(); self.calendar.setSelectedDate(QDate.currentDate()); self.calendar.selectionChanged.connect(self._select_day)
        self.calendar.currentPageChanged.connect(lambda *_: self.refresh())
        cal_layout.addWidget(self.calendar); body.addWidget(calendar_card, 13)
        detail_card = QWidget(objectName="card"); detail = QVBoxLayout(detail_card); detail.setContentsMargins(16, 16, 16, 16)
        self.day_title = QLabel(objectName="cardTitle"); self.day_summary = QLabel(objectName="helperText")
        detail.addWidget(self.day_title); detail.addWidget(self.day_summary)
        self.task_area = QScrollArea(objectName="calendarTaskArea"); self.task_area.setWidgetResizable(True); self.task_container = QWidget(objectName="calendarTaskContainer"); self.task_layout = QVBoxLayout(self.task_container); self.task_layout.setContentsMargins(0, 4, 0, 4)
        self.task_area.setWidget(self.task_container); detail.addWidget(self.task_area, 1)
        manual = QPushButton("+ 添加临时任务"); manual.clicked.connect(self.add_manual); detail.addWidget(manual)
        body.addWidget(detail_card, 7); root.addWidget(body_widget, 1)
        review_card = QWidget(objectName="card"); review_layout = QVBoxLayout(review_card); review_layout.setContentsMargins(16, 12, 16, 12); review_layout.setSpacing(8)
        review_header = QHBoxLayout(); review_header.addWidget(QLabel("待评价", objectName="cardTitle"))
        self.review_count = QLabel("0", objectName="countLabel"); review_header.addWidget(self.review_count); review_header.addStretch()
        review_layout.addLayout(review_header)
        self.review_area = QScrollArea(objectName="pendingReviewArea")
        self.review_area.setWidgetResizable(True)
        self.review_area.setMinimumHeight(116); self.review_area.setMaximumHeight(176)
        self.review_container = QWidget(objectName="pendingReviewList")
        self.review_layout = QVBoxLayout(self.review_container); self.review_layout.setContentsMargins(0, 0, 0, 0); self.review_layout.setSpacing(0)
        self.review_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.review_area.setWidget(self.review_container); review_layout.addWidget(self.review_area); root.addWidget(review_card)

    def _range(self) -> tuple[date, date]:
        shown = date(self.calendar.yearShown(), self.calendar.monthShown(), 1)
        next_month = (shown.replace(day=28) + timedelta(days=4)).replace(day=1)
        return shown, next_month - timedelta(days=1)

    def refresh(self) -> None:
        start, end = self._range()
        month_tasks = self._filtered(self.calendar_data.tasks_between(start, end))
        grouped: dict[str, list[dict]] = {}
        for task in month_tasks: grouped.setdefault(task["date"], []).append(task)
        self.calendar.tasks = grouped; self.calendar.updateCells()
        self.month_label.setText(f"{self.calendar.yearShown()}年{self.calendar.monthShown()}月")
        self._refresh_day(); self._refresh_reviews(); self._refresh_stats()

    def _filtered(self, tasks: list[dict]) -> list[dict]:
        selected = self.platform_filter.currentData()
        return tasks if selected == "all" else [task for task in tasks if task.get("platform") == selected]

    def _select_day(self) -> None:
        self.selected_day = as_date(self.calendar.selectedDate()); self._refresh_day()

    def _refresh_day(self) -> None:
        tasks = self._filtered(self.calendar_data.tasks_between(self.selected_day, self.selected_day))
        suffix = " · 今天" if self.selected_day == date.today() else ""
        self.day_title.setText(f"{self.selected_day.month}月{self.selected_day.day}日{suffix}")
        completed = sum(task_status(t["target_quantity"], t["actual_quantity"], self.selected_day) == "completed" for t in tasks)
        self.day_summary.setText(f"任务 {len(tasks)} 个 · 已完成 {completed} / {len(tasks)}")
        while self.task_layout.count():
            item = self.task_layout.takeAt(0)
            if item.widget(): item.widget().hide(); item.widget().deleteLater()
        if not tasks:
            next_tasks = self._filtered(self.calendar_data.tasks_between(self.selected_day + timedelta(days=1), self.selected_day + timedelta(days=31)))
            empty = EmptyState()
            empty.action_requested.connect(self.add_plan)
            if next_tasks:
                next_day = parse_date(next_tasks[0]["date"])
                empty.configure("今天没有出单计划" if self.selected_day == date.today() else "当天没有出单计划",
                                f"下一计划\n{next_day.month}月{next_day.day}日 · {platform_name(next_tasks[0])} · {next_tasks[0]['model']}")
            elif not self.calendar_data.plans:
                empty.configure("暂无计划", "创建商品计划后，会在日历中显示出单日期。", action=True)
            else:
                empty.configure("今天没有出单计划" if self.selected_day == date.today() else "当天没有出单计划")
            self.task_layout.addWidget(empty)
        for task in sorted(tasks, key=self._sort_key): self.task_layout.addWidget(self._task_card(task))
        self.task_layout.addStretch()

    def _task_card(self, task: dict) -> QWidget:
        card = QWidget(objectName="card"); layout = QVBoxLayout(card); layout.setContentsMargins(12, 10, 12, 10); layout.setSpacing(5)
        layout.addWidget(QLabel(f"【{platform_name(task)}】 {task['model']}", objectName="cardTitle"))
        status = task_status(task["target_quantity"], task["actual_quantity"], parse_date(task["date"]))
        labels = {"pending": "待完成", "missed": "未完成", "partial": "部分完成", "completed": "✓ 已完成"}
        layout.addWidget(QLabel(f"计划：{task['target_quantity']}单　实际：{task['actual_quantity']}单　{labels[status]}", objectName="statusText"))
        if task["actual_quantity"]:
            review = review_status(task["actual_quantity"], task["reviewed_quantity"])
            review_text = {"unreviewed": "未评价", "reviewed": "已评价", "partial": f"部分评价 {task['reviewed_quantity']}/{task['actual_quantity']}"}[review]
            layout.addWidget(QLabel(f"评价：{review_text}", objectName="statusText"))
        actions = QHBoxLayout()
        if status != "completed":
            finish = QPushButton("完成", objectName="primary"); finish.clicked.connect(lambda _=False, item=task: self.complete(item)); actions.addWidget(finish)
        if task["actual_quantity"] > task["reviewed_quantity"]:
            reviewed = QPushButton("标记已评价"); reviewed.clicked.connect(lambda _=False, item=task: self.mark_reviewed(item)); actions.addWidget(reviewed)
        edit = QPushButton("编辑"); edit.clicked.connect(lambda _=False, item=task: self.edit_task(item)); actions.addWidget(edit); actions.addStretch(); layout.addLayout(actions)
        return card

    @staticmethod
    def _sort_key(task: dict) -> tuple:
        status = task_status(task["target_quantity"], task["actual_quantity"], parse_date(task["date"]))
        review = review_status(task["actual_quantity"], task["reviewed_quantity"])
        return ({"pending": 0, "missed": 0, "partial": 1, "completed": 2}[status], review == "reviewed", task["model"])

    def _refresh_reviews(self) -> None:
        while self.review_layout.count():
            item = self.review_layout.takeAt(0)
            if item.widget(): item.widget().hide(); item.widget().deleteLater()
        tasks = self._filtered(self.calendar_data.pending_reviews())
        self.review_count.setText(str(len(tasks)))
        if not tasks:
            empty = QWidget(objectName="reviewEmpty")
            layout = QVBoxLayout(empty); layout.setContentsMargins(0, 8, 0, 10); layout.setSpacing(3)
            layout.addWidget(QLabel("暂无待评价记录", objectName="emptyTitle"))
            layout.addWidget(QLabel("已经完成出单但尚未评价的记录，会显示在这里。", objectName="emptyHint"))
            self.review_layout.addWidget(empty)
            return
        for task in tasks:
            row = QWidget(objectName="reviewRow")
            layout = QHBoxLayout(row); layout.setContentsMargins(0, 8, 0, 8); layout.setSpacing(12)
            name = QPushButton(f"{platform_name(task)} · {task['model']}", objectName="reviewName")
            name.clicked.connect(lambda _=False, value=task["date"]: self.open_review_item(value))
            status = "未评价" if not task["reviewed_quantity"] else f"已评价 {task['reviewed_quantity']} / {task['actual_quantity']}"
            layout.addWidget(name)
            layout.addWidget(QLabel(f"{task['date'][5:].replace('-', '/')} 出单", objectName="reviewDate"))
            layout.addWidget(QLabel(status, objectName="reviewStatus"))
            layout.addStretch()
            action = QPushButton("标记已评价" if not task["reviewed_quantity"] else "更新")
            action.clicked.connect(lambda _=False, item=task: self.mark_reviewed(item))
            layout.addWidget(action)
            self.review_layout.addWidget(row)

    def _refresh_stats(self) -> None:
        today_tasks = self._filtered(self.calendar_data.tasks_between(date.today(), date.today()))
        completed = sum(task_status(t["target_quantity"], t["actual_quantity"], date.today()) == "completed" for t in today_tasks)
        historical = self._filtered(self.calendar_data.tasks_between(date.min, date.today() - timedelta(days=1)))
        missed = sum(task_status(t["target_quantity"], t["actual_quantity"], parse_date(t["date"])) == "missed" for t in historical)
        for label, value in zip(self.stats, (len(today_tasks), completed, missed, len(self._filtered(self.calendar_data.pending_reviews())))): label.setText(str(value))

    def _move_month(self, offset: int) -> None:
        self.calendar.showNextMonth() if offset > 0 else self.calendar.showPreviousMonth()

    def go_today(self) -> None:
        self.calendar.showToday(); self.calendar.setSelectedDate(QDate.currentDate()); self.selected_day = date.today(); self.refresh()

    def add_plan(self) -> None:
        if PlanDialog(self.calendar_data, parent=self).exec(): self.refresh()

    def manage_plans(self) -> None:
        dialog = PlanManagerDialog(self.calendar_data, self); dialog.changed.connect(self.refresh); dialog.exec(); self.refresh()

    def add_manual(self) -> None:
        if TaskDialog(self.calendar_data, self.selected_day, parent=self).exec(): self.refresh()

    def edit_task(self, task: dict) -> None:
        if TaskDialog(self.calendar_data, parse_date(task["date"]), task, self).exec(): self.refresh()

    def complete(self, task: dict) -> None:
        self.calendar_data.upsert_record(task.get("plan_id"), parse_date(task["date"]), record_id=task.get("id"), source=task["source"],
                                         platform=task["platform"], custom_platform_name=task.get("custom_platform_name", ""), model=task["model"],
                                         target_quantity=task["target_quantity"], actual_quantity=task["target_quantity"],
                                         reviewed_quantity=task["reviewed_quantity"], note=task.get("note", "")); self.refresh()

    def mark_reviewed(self, task: dict) -> None:
        self.calendar_data.upsert_record(task.get("plan_id"), parse_date(task["date"]), record_id=task.get("id"), source=task["source"],
                                         platform=task["platform"], custom_platform_name=task.get("custom_platform_name", ""), model=task["model"],
                                         target_quantity=task["target_quantity"], actual_quantity=task["actual_quantity"],
                                         reviewed_quantity=task["actual_quantity"], review_date=date.today().isoformat(), note=task.get("note", "")); self.refresh()

    def open_review_item(self, value: str) -> None:
        day = parse_date(value); self.calendar.setCurrentPage(day.year, day.month); self.calendar.setSelectedDate(as_qdate(day)); self.selected_day = day; self.refresh()
