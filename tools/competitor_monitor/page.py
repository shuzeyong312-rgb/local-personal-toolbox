from __future__ import annotations

import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, QSettings, Qt, QTime, Signal
from PySide6.QtGui import QDesktopServices, QTextLayout, QTextOption
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QAbstractItemView, QButtonGroup, QDateEdit, QFrame, QGridLayout, QListWidget, QMenu,
    QPlainTextEdit, QProgressBar, QPushButton, QStackedLayout, QTableWidget,
    QTableWidgetItem, QTabWidget, QToolButton,
    QVBoxLayout, QWidget,
)

from components.dialogs import BaseDialog
from app.icons import icon
from services.competitor_monitor import ChromeEnvironment, MonitorStore
from services.competitor_monitor_auto import TaskScheduler
from tools.competitor_monitor.worker import CollectionWorker


class ProductCell(QWidget):
    """A fixed-height product cell that keeps long names readable without growing table rows."""

    def __init__(self, name: str, shop_name: str, group_name: str, parent=None) -> None:
        super().__init__(parent)
        self.name = name
        self.title = QLabel(objectName="productTitle")
        self.title.setWordWrap(True)
        self.title.setFixedHeight(self.title.fontMetrics().lineSpacing() * 2)
        self.meta = QLabel(f"{shop_name} · {group_name}", objectName="productMeta")
        self.meta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setToolTip(f"{name}\n{shop_name} · {group_name}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 7)
        layout.setSpacing(2)
        layout.addWidget(self.title)
        layout.addWidget(self.meta)
        self._update_title()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_title()

    def text(self) -> str:
        """Compatibility with the previous QLabel-backed table cell."""
        return f"{self.title.text()}\n{self.meta.text()}"

    def _update_title(self) -> None:
        width = max(1, self.width() - 24)
        layout = QTextLayout(self.name, self.title.font())
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(option)
        layout.beginLayout()
        lines = []
        for _ in range(2):
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(width)
            lines.append((line.textStart(), line.textLength()))
        layout.endLayout()
        if not lines:
            self.title.setText("")
            return
        shown = [self.name[start:start + length] for start, length in lines]
        end = lines[-1][0] + lines[-1][1]
        if end < len(self.name):
            shown[-1] = self.title.fontMetrics().elidedText(
                self.name[lines[-1][0]:], Qt.TextElideMode.ElideRight, width
            )
        elif len(self.name) > 32:
            # ponytail: headless fallback assumes 16 CJK chars/line; use a measured delegate if font metrics stay unreliable.
            shown = [self.name[:16], f"{self.name[16:31]}…"]
        self.title.setText("\n".join(shown))


class MonitorTimeField(QLineEdit):
    """A time field with the QTimeEdit read API but without native spin buttons."""

    timeChanged = Signal(QTime)

    def __init__(self, value: QTime, parent=None) -> None:
        super().__init__(parent, objectName="monitorTime")
        self._time = value
        self.setInputMask("00:00")
        self.setTime(value)
        self.editingFinished.connect(self._commit)

    def time(self) -> QTime:
        return self._time

    def setTime(self, value: QTime) -> None:
        self._time = value
        self.setText(value.toString("HH:mm"))

    def _commit(self) -> None:
        value = QTime.fromString(self.text(), "HH:mm")
        if not value.isValid():
            self.setText(self._time.toString("HH:mm"))
            return
        if value != self._time:
            self._time = value
            self.timeChanged.emit(value)


class MonitorNumberField(QLineEdit):
    """A bounded numeric input that keeps the existing spin-box value API without native chrome."""

    def __init__(self, *, integer=False, parent=None) -> None:
        super().__init__(parent, objectName="monitorNumber")
        self.integer = integer
        self.minimum, self.maximum, self.suffix, self._value = 0, 0, "", 0
        self.editingFinished.connect(self._commit)

    def setRange(self, minimum, maximum) -> None:
        self.minimum, self.maximum = minimum, maximum

    def setSuffix(self, suffix: str) -> None:
        self.suffix = suffix

    def setValue(self, value) -> None:
        value = int(value) if self.integer else float(value)
        self._value = max(self.minimum, min(self.maximum, value))
        shown = str(int(self._value)) if self.integer else f"{self._value:g}"
        self.setText(f"{shown}{self.suffix}")

    def value(self):
        return self._value

    def _commit(self) -> None:
        raw = self.text().removesuffix(self.suffix).strip()
        try:
            self.setValue(int(raw) if self.integer else float(raw))
        except ValueError:
            self.setValue(self._value)


def dialog_footer(actions: QHBoxLayout) -> QWidget:
    footer = QWidget(objectName="dialogFooter")
    footer.setLayout(actions)
    return footer


class MessageDialog(BaseDialog):
    def __init__(self, title: str, message: str, parent=None, *, confirm=False,
                 details: str = "", open_browser=False) -> None:
        super().__init__(title, parent)
        self.setMinimumWidth(540)
        text = QLabel(message); text.setWordWrap(True); self.layout.addWidget(text)
        if details:
            toggle = QPushButton("查看详情")
            detail = QPlainTextEdit(details, objectName="failureDetails"); detail.setReadOnly(True); detail.hide()
            toggle.clicked.connect(lambda: (detail.setVisible(not detail.isVisible()), toggle.setText("收起详情" if detail.isVisible() else "查看详情")))
            self.layout.addWidget(toggle); self.layout.addWidget(detail)
        actions = QHBoxLayout(); actions.addStretch()
        if open_browser:
            button = QPushButton("打开专用浏览器")
            button.clicked.connect(self._open_browser)
            actions.addWidget(button)
        cancel = QPushButton("取消" if confirm else "关闭")
        cancel.clicked.connect(self.reject if confirm else self.accept); actions.addWidget(cancel)
        if confirm:
            accept = QPushButton("删除", objectName="primary"); accept.clicked.connect(self.accept); actions.addWidget(accept)
        self.layout.addWidget(dialog_footer(actions))

    def _open_browser(self) -> None:
        try:
            ChromeEnvironment().open_browser()
        except Exception as exc:
            MessageDialog("无法打开专用浏览器", "请检查 Chrome 是否正常安装。", self, details=str(exc)).exec()


class TextInputDialog(BaseDialog):
    def __init__(self, title: str, label: str, value: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self.layout.addWidget(QLabel(label))
        self.input = QLineEdit(value); self.layout.addWidget(self.input)
        actions = QHBoxLayout(); actions.addStretch()
        cancel = QPushButton("取消"); save = QPushButton("保存", objectName="primary")
        cancel.clicked.connect(self.reject); save.clicked.connect(self.accept)
        actions.addWidget(cancel); actions.addWidget(save); self.layout.addWidget(dialog_footer(actions))


class CompetitorDialog(BaseDialog):
    def __init__(self, store: MonitorStore, competitor=None, parent=None) -> None:
        super().__init__("编辑竞品" if competitor else "添加竞品", parent)
        self.setMinimumWidth(620)
        form = QFormLayout()
        if competitor:
            self.urls = None
        else:
            self.urls = QPlainTextEdit(placeholderText="每行粘贴一个1688商品详情链接")
            form.addRow("商品链接", self.urls)
        self.group = QComboBox()
        self.group.addItem("未分组", None)
        for row in store.groups(): self.group.addItem(row["name"], row["id"])
        self.alias = QLineEdit(competitor["alias"] or "" if competitor else "")
        self.note = QPlainTextEdit(competitor["note"] or "" if competitor else "")
        self.note.setMaximumHeight(80)
        form.addRow("竞品组", self.group)
        form.addRow("自定义名称", self.alias)
        form.addRow("备注", self.note)
        if competitor:
            self.group.setCurrentIndex(max(0, self.group.findData(competitor["group_id"])))
        self.layout.addLayout(form)
        actions = QHBoxLayout(); actions.addStretch()
        cancel = QPushButton("取消"); save = QPushButton("保存", objectName="primary")
        cancel.clicked.connect(self.reject); save.clicked.connect(self.accept)
        actions.addWidget(cancel); actions.addWidget(save); self.layout.addWidget(dialog_footer(actions))

    def values(self):
        return self.group.currentData(), self.alias.text(), self.note.toPlainText()


class CollectionProgress(BaseDialog):
    def __init__(self, total: int, parent=None) -> None:
        super().__init__("立即采集", parent)
        self.setMinimumWidth(650)
        self.label = QLabel(f"准备采集 {total} 个商品")
        progress_shell = QWidget(objectName="monitorProgress")
        stack = QStackedLayout(progress_shell); stack.setStackingMode(QStackedLayout.StackingMode.StackAll); stack.setContentsMargins(0, 0, 0, 0)
        self.bar = QProgressBar(objectName="monitorProgressBar"); self.bar.setRange(0, total); self.bar.setTextVisible(False); self.bar.setMinimumHeight(26)
        self.percent = QLabel("0%", objectName="monitorProgressText", alignment=Qt.AlignmentFlag.AlignCenter)
        stack.addWidget(self.bar); stack.addWidget(self.percent); stack.setCurrentWidget(self.percent)
        self.cancel = QPushButton("取消剩余任务")
        self.layout.addWidget(self.label); self.layout.addWidget(progress_shell); self.layout.addWidget(self.cancel, alignment=Qt.AlignmentFlag.AlignRight)

    def update_progress(self, completed: int, total: int) -> None:
        self.bar.setRange(0, total); self.bar.setValue(completed)
        self.percent.setText(f"{round(completed * 100 / total) if total else 0}%")

    def set_state(self, state: str) -> None:
        self.label.setText(state)

    def set_current(self, index: int, total: int, name: str) -> None:
        shown = self.label.fontMetrics().elidedText(name, Qt.TextElideMode.ElideRight, 560)
        self.label.setText(f"正在监控 {index} / {total}\n当前：{shown}")


class GroupManagerDialog(BaseDialog):
    def __init__(self, store: MonitorStore, parent=None) -> None:
        super().__init__("管理分组", parent)
        self.store = store; self.changed = False; self.setMinimumWidth(520)
        self.groups = QListWidget(); self.layout.addWidget(self.groups)
        actions = QHBoxLayout()
        for label, slot in (("新建", self.add_group), ("重命名", self.rename_group), ("删除", self.delete_group)):
            button = QPushButton(label); button.clicked.connect(slot); actions.addWidget(button)
        actions.addStretch(); close = QPushButton("关闭", objectName="primary"); close.clicked.connect(self.accept); actions.addWidget(close)
        self.layout.addWidget(dialog_footer(actions)); self.refresh()

    def refresh(self) -> None:
        self.groups.clear()
        for row in self.store.groups():
            self.groups.addItem(row["name"]); self.groups.item(self.groups.count() - 1).setData(Qt.ItemDataRole.UserRole, row["id"])

    def add_group(self) -> None:
        dialog = TextInputDialog("新建分组", "分组名称", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try: self.store.add_group(dialog.input.text()); self.changed = True; self.refresh()
            except (ValueError, sqlite3.IntegrityError) as exc: MessageDialog("无法新建", str(exc), self).exec()

    def rename_group(self) -> None:
        item = self.groups.currentItem()
        if not item: return
        dialog = TextInputDialog("重命名分组", "新名称", item.text(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try: self.store.rename_group(item.data(Qt.ItemDataRole.UserRole), dialog.input.text()); self.changed = True; self.refresh()
            except (ValueError, sqlite3.IntegrityError) as exc: MessageDialog("无法重命名", str(exc), self).exec()

    def delete_group(self) -> None:
        item = self.groups.currentItem()
        if item and MessageDialog("删除分组", "商品将移动到“未分组”，继续吗？", self, confirm=True).exec() == QDialog.DialogCode.Accepted:
            self.store.delete_group(item.data(Qt.ItemDataRole.UserRole)); self.changed = True; self.refresh()


class HistoryDialog(BaseDialog):
    def __init__(self, store: MonitorStore, competitor_id: int, parent=None) -> None:
        competitor = store.competitor(competitor_id)
        super().__init__(competitor["alias"] or competitor["title"] or competitor["offer_id"], parent)
        self.store = store; self.competitor_id = competitor_id; self.setMinimumSize(1000, 700)
        meta = QLabel(f"{competitor['shop_name'] or '店铺未知'}  ·  {competitor['status']}  ·  最近采集 {format_time(competitor['last_attempt_at'], full=True)}", objectName="monitorMeta")
        meta.setWordWrap(True); self.layout.addWidget(meta)
        link = QPushButton("打开 1688 商品链接", objectName="linkButton")
        link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(competitor["url"])))
        self.layout.addWidget(link, alignment=Qt.AlignmentFlag.AlignLeft)
        toolbar = QHBoxLayout(); toolbar.addWidget(QLabel("时间范围"))
        self.range_group = QButtonGroup(self); self.range_group.setExclusive(True)
        self.range = QComboBox(); self.range.hide()  # compatibility with existing callers
        for index, (label, days) in enumerate((("7天", 7), ("30天", 30), ("90天", 90), ("365天", 365))):
            button = QPushButton(label, objectName="segmentButton"); button.setCheckable(True)
            button.setProperty("days", days); self.range_group.addButton(button); toolbar.addWidget(button)
            if index == 0: button.setChecked(True)
        self.range_group.buttonClicked.connect(self.refresh); toolbar.addStretch(); self.layout.addLayout(toolbar)
        metrics = QHBoxLayout(); self.metric_labels = []
        for title in ("当前价格", "页面已售", "月成交", "SKU数量", "最近采集"):
            card, value = metric_card(title); metrics.addWidget(card); self.metric_labels.append(value)
        self.layout.addLayout(metrics)
        trends = QHBoxLayout()
        for title in ("价格趋势", "页面已售趋势", "月成交趋势"):
            box = card_widget(); column = QVBoxLayout(box); column.addWidget(QLabel(title, objectName="cardTitle"))
            column.addWidget(QLabel("折线图区域\n数据已按日期准备", objectName="trendPlaceholder"), 1); trends.addWidget(box)
        self.layout.addLayout(trends)
        self.history = QTableWidget(0, 5, objectName="previewTable")
        self.history.setHorizontalHeaderLabels(("日期", "价格", "页面已售", "月成交", "SKU数量"))
        configure_table(self.history, [150, 160, 140, 140, 110], stretch=0)
        self.layout.addWidget(QLabel("历史快照", objectName="sectionTitle")); self.layout.addWidget(self.history, 1)
        self.timeline = QTableWidget(0, 3, objectName="previewTable")
        self.timeline.setHorizontalHeaderLabels(("时间", "变化", "详情"))
        configure_table(self.timeline, [150, 160, 520], stretch=2)
        self.layout.addWidget(QLabel("变化时间线", objectName="sectionTitle")); self.layout.addWidget(self.timeline, 1)
        close = QPushButton("关闭", objectName="primary"); close.clicked.connect(self.accept)
        footer = QHBoxLayout(); footer.addStretch(); footer.addWidget(close)
        self.layout.addWidget(dialog_footer(footer)); self.refresh()

    def refresh(self) -> None:
        days = self.range_group.checkedButton().property("days")
        rows = self.store.daily_history(self.competitor_id, days)
        self.history.setRowCount(len(rows))
        for index, row in enumerate(rows):
            price = "--" if row["display_price_min"] is None else (
                f"¥{row['display_price_min']:g}" if row["display_price_min"] == row["display_price_max"]
                else f"¥{row['display_price_min']:g}–¥{row['display_price_max']:g}"
            )
            values = (row["snapshot_date"], price, row["sales_raw"] or "--", row["month_sales_raw"] or "--",
                      str(len(_json_field(row, "visible_sku_names_json"))))
            for column, value in enumerate(values): self.history.setItem(index, column, QTableWidgetItem(value))
        snapshot = self.store.latest_snapshot(self.competitor_id)
        current = (_prices(snapshot), _field(snapshot, "sales_raw"), _field(snapshot, "month_sales_raw"),
                   str(len(_json_field(snapshot, "visible_sku_names_json"))), format_time(_field(snapshot, "collected_at"), full=True))
        for label, value in zip(self.metric_labels, current): label.setText(value)
        events = [row for row in self.store.events() if row["competitor_id"] == self.competitor_id
                  and row["created_at"][:10] >= (rows[0]["snapshot_date"] if rows else "9999-12-31")]
        self.timeline.setRowCount(len(events))
        for index, event in enumerate(events):
            shown = format_event_detail(event)
            for column, value in enumerate((format_time(event["created_at"], full=True), event["title"], shown)):
                self.timeline.setItem(index, column, QTableWidgetItem(value))


class CompetitorMonitorPage(QWidget):
    def __init__(self, db_path: Path | str = Path("data/competitor_monitor.db")) -> None:
        super().__init__(objectName="page")
        self.store = MonitorStore(db_path)
        self.settings = QSettings("LocalToolbox", "competitor_monitor")
        self.worker = None
        root = QVBoxLayout(self); root.setContentsMargins(24, 18, 24, 22); root.setSpacing(14)
        hero = QFrame(objectName="monitorHero")
        hero_layout = QHBoxLayout(hero); hero_layout.setContentsMargins(24, 18, 24, 18); hero_layout.setSpacing(16)
        hero_copy = QVBoxLayout(); hero_copy.setSpacing(4)
        hero_copy.addWidget(QLabel("COMPETITOR INTELLIGENCE", objectName="monitorEyebrow"))
        hero_copy.addWidget(QLabel("1688竞品监控", objectName="monitorPageTitle"))
        hero_copy.addWidget(QLabel("追踪公开页面快照，聚焦价格、SKU 与销售指标变化", objectName="monitorPageSubtitle"))
        hero_layout.addLayout(hero_copy, 1)
        hero_status = QVBoxLayout(); hero_status.setSpacing(6)
        live = QLabel("●  本地数据监控", objectName="monitorLive")
        live.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_status.addWidget(live, alignment=Qt.AlignmentFlag.AlignRight)
        hero_status.addWidget(QLabel("公开页面快照 · 数据不上传", objectName="monitorHeroHint"), alignment=Qt.AlignmentFlag.AlignRight)
        hero_layout.addLayout(hero_status)
        root.addWidget(hero)
        self.tabs = QTabWidget(objectName="monitorTabs"); root.addWidget(self.tabs, 1)

        dashboard = QWidget(); dashboard_layout = QVBoxLayout(dashboard); dashboard_layout.setContentsMargins(0, 16, 0, 0)
        self.summary = QLabel(); self.summary.hide()  # machine-readable summary retained for compatibility
        stats = QHBoxLayout(); self.stat_values = []
        for title, tone in (("监控商品", "primary"), ("今日成功", "cyan"), ("价格变化", "violet"), ("销量异常", "orange"), ("采集异常", "rose")):
            card, value = metric_card(title, tone); stats.addWidget(card); self.stat_values.append(value)
        dashboard_layout.addLayout(stats)
        dashboard_layout.addWidget(QLabel("今日变化", objectName="sectionTitle"))
        self.today_empty = QLabel("今日暂无变化\n完成采集后，价格、销量和 SKU 变化会显示在这里。", objectName="monitorEmpty")
        self.today_empty.setAlignment(Qt.AlignmentFlag.AlignCenter); dashboard_layout.addWidget(self.today_empty, 1)
        self.today_table = QTableWidget(0, 5, objectName="monitorTable")
        self.today_table.setHorizontalHeaderLabels(("时间", "商品", "变化类型", "变化", "变化幅度"))
        configure_table(self.today_table, [90, 300, 140, 230, 150], stretch=1)
        self.today_table.cellDoubleClicked.connect(lambda row, _column: self.open_event_product(self.today_table, row))
        dashboard_layout.addWidget(self.today_table, 1); self.tabs.addTab(dashboard, "今日监控")

        products = QWidget(); product_layout = QVBoxLayout(products); product_layout.setContentsMargins(0, 16, 0, 0)

        toolbar_card = QFrame(objectName="monitorToolbar")
        toolbar = QHBoxLayout(toolbar_card)
        toolbar.setContentsMargins(14, 12, 14, 12)
        toolbar.setSpacing(10)
        add = QPushButton("添加竞品", objectName="monitorPrimary"); add.setIcon(icon("plus", "#FFFFFF")); add.clicked.connect(self.add_competitors)
        collect = QPushButton("立即采集", objectName="monitorCollect"); collect.setIcon(icon("monitor", "#2563EB")); collect.clicked.connect(self.collect_all)
        self.group_filter = QComboBox(); self.group_filter.setMinimumWidth(138); self.group_filter.currentIndexChanged.connect(self.refresh)
        self.product_search = QLineEdit(); self.product_search.setObjectName("monitorSearch"); self.product_search.setPlaceholderText("搜索商品或店铺"); self.product_search.setMinimumWidth(180)
        self.product_search.textChanged.connect(self.refresh)
        self.only_changed = QCheckBox("仅看有变化", objectName="filterChip"); self.only_changed.toggled.connect(self.refresh)
        self.only_failed = QCheckBox("仅看采集异常", objectName="filterChip"); self.only_failed.toggled.connect(self.refresh)
        manage = QPushButton("管理分组", objectName="monitorQuiet"); manage.clicked.connect(self.manage_groups)
        self.cdp = QLineEdit(str(self.settings.value("cdp_url", "http://127.0.0.1:9222")))
        self.cdp.setMaximumWidth(220); self.cdp.editingFinished.connect(lambda: self.settings.setValue("cdp_url", self.cdp.text().strip()))
        toolbar.addWidget(self.product_search, 1)
        toolbar.addWidget(self.group_filter)
        toolbar.addWidget(self.only_changed)
        toolbar.addWidget(self.only_failed)
        toolbar.addWidget(manage)
        toolbar.addWidget(collect)
        toolbar.addWidget(add)
        product_layout.addWidget(toolbar_card)

        self.table = QTableWidget(0, 8, objectName="monitorTable")
        self.table.setHorizontalHeaderLabels(("商品", "价格", "页面已售", "月成交", "SKU", "最近变化", "状态", "操作"))
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.cellDoubleClicked.connect(lambda _row, _column: self.open_history())
        configure_table(self.table, [260, 105, 85, 85, 58, 125, 80, 54], stretch=0)
        product_layout.addWidget(self.table, 1)

        self.batch_bar = card_widget("batchBar"); actions = QHBoxLayout(self.batch_bar); actions.setContentsMargins(12, 8, 12, 8)
        self.batch_count = QLabel(); actions.addWidget(self.batch_count)
        for label, slot in (("采集选中", self.collect_selected), ("暂停/恢复", self.toggle_selected), ("删除", self.delete_selected)):
            button = QPushButton(label); button.clicked.connect(slot); actions.addWidget(button)
        actions.addStretch(); self.batch_bar.hide(); product_layout.addWidget(self.batch_bar)
        self.detail = QLabel("选择商品查看最近快照", objectName="helperText")
        self.detail.setWordWrap(True); product_layout.addWidget(self.detail)
        self.detail_button = QPushButton("查看详情")
        self.detail_button.clicked.connect(self._show_failure_details); self.detail_button.hide()
        product_layout.addWidget(self.detail_button, alignment=Qt.AlignmentFlag.AlignLeft); self.detail.hide(); self.detail_button.hide()
        self.tabs.addTab(products, "竞品商品")

        events = QWidget(); events_layout = QVBoxLayout(events); events_layout.setContentsMargins(0, 16, 0, 0)
        filter_card = QFrame(objectName="monitorToolbar"); filters = QHBoxLayout(filter_card); filters.setContentsMargins(14, 12, 14, 12); filters.setSpacing(10)
        self.event_type = QComboBox(); self.event_type.addItem("全部事件", None)
        for label, value in (("价格变化", "price_change"), ("价格结构变化", "price_structure_change"),
                             ("SKU新增", "sku_added"), ("SKU删除", "sku_removed"),
                             ("页面已售变化", "sales_metric_jump"), ("助手指标变化", "metric_change"),
                             ("采集部分异常", "collection_partial"), ("采集失败", "collection_failed")):
            self.event_type.addItem(label, value)
        self.event_type.currentIndexChanged.connect(self.refresh_events)
        self.event_group = QComboBox(); self.event_group.currentIndexChanged.connect(self.refresh_events)
        self.event_date = QDateEdit(QDate.currentDate().addDays(-30), objectName="monitorDate"); self.event_date.setCalendarPopup(True); self.event_date.setDisplayFormat("yyyy-MM-dd")
        self.event_end = QDateEdit(QDate.currentDate(), objectName="monitorDate"); self.event_end.setCalendarPopup(True); self.event_end.setDisplayFormat("yyyy-MM-dd")
        self.event_search = QLineEdit(); self.event_search.setPlaceholderText("搜索商品"); self.event_search.textChanged.connect(self.refresh_events)
        self.event_date.dateChanged.connect(self.refresh_events); self.event_end.dateChanged.connect(self.refresh_events)
        filters.addWidget(QLabel("类型")); filters.addWidget(self.event_type)
        filters.addWidget(QLabel("分组")); filters.addWidget(self.event_group)
        filters.addWidget(QLabel("日期范围")); filters.addWidget(self.event_date); filters.addWidget(QLabel("至")); filters.addWidget(self.event_end)
        filters.addWidget(self.event_search, 1)
        events_layout.addWidget(filter_card)
        self.events_table = QTableWidget(0, 5, objectName="monitorTable")
        self.events_table.setHorizontalHeaderLabels(("时间", "商品", "事件", "变化", "状态"))
        configure_table(self.events_table, [150, 300, 150, 330, 90], stretch=1)
        self.events_table.cellDoubleClicked.connect(lambda row, _column: self.open_event_product(self.events_table, row))
        events_layout.addWidget(self.events_table, 1); self.tabs.addTab(events, "异常事件")

        settings_page = QWidget(); settings_layout = QVBoxLayout(settings_page); settings_layout.setContentsMargins(0, 16, 0, 0)
        self.scheduled_time = MonitorTimeField(QTime.fromString(str(self.settings.value("scheduled_time", "09:00")), "HH:mm"))
        self.catch_up = QCheckBox("电脑错过计划时间后，在当天登录时补采一次")
        self.catch_up.setChecked(self.settings.value("catch_up", True, type=bool))
        self.notifications = QCheckBox("启用 Windows 桌面通知")
        self.notifications.setChecked(self.settings.value("notification_enabled", True, type=bool))
        self.price_threshold = MonitorNumberField(); self.price_threshold.setRange(0.1, 100)
        self.price_threshold.setSuffix(" %"); self.price_threshold.setValue(float(self.settings.value("price_threshold", 5)))
        self.sales_threshold = MonitorNumberField(integer=True); self.sales_threshold.setRange(1, 1000000)
        self.sales_threshold.setValue(int(self.settings.value("sales_threshold", 20)))
        self.schedule_enabled = QCheckBox("启用自动采集"); self.schedule_enabled.setChecked(self.settings.value("schedule_enabled", False, type=bool))
        self.retention = QComboBox(); self.retention.addItems(("永久保留", "保留 365 天", "保留 180 天", "保留 90 天"))
        grid = QGridLayout(); grid.setSpacing(12)
        grid.addWidget(settings_card("自动采集", (("每日采集时间", self.scheduled_time), ("开机后补采", self.catch_up), ("", self.schedule_enabled))), 0, 0)
        grid.addWidget(settings_card("异常提醒", (("价格变化提醒阈值", self.price_threshold), ("销量展示下界变化提醒阈值", self.sales_threshold), ("", self.notifications))), 0, 1)
        grid.addWidget(settings_card("高级设置", (("Chrome 调试地址", self.cdp), ("数据保留策略", self.retention))), 1, 0, 1, 2)
        settings_layout.addLayout(grid)
        settings_actions = QHBoxLayout()
        enable = QPushButton("保存设置", objectName="primary"); enable.clicked.connect(self.save_settings)
        settings_actions.addWidget(enable); settings_actions.addStretch()
        settings_layout.addLayout(settings_actions)
        self.schedule_status = QLabel("自动采集由 Windows 任务计划执行，工具界面无需保持打开。", objectName="helperText")
        settings_layout.addWidget(self.schedule_status); settings_layout.addStretch()
        self.tabs.addTab(settings_page, "设置")
        self._failure_details = None
        self.refresh_groups(); self.refresh()

    def close(self) -> None:
        self.stop_worker(); self.store.close(); super().close()

    def stop_worker(self) -> None:
        if self.worker and self.worker.isRunning(): self.worker.cancel(); self.worker.wait(5000)

    def refresh_groups(self) -> None:
        current = self.group_filter.currentData()
        self.group_filter.blockSignals(True); self.group_filter.clear(); self.group_filter.addItem("全部", None)
        for row in self.store.groups(): self.group_filter.addItem(row["name"], row["id"])
        self.group_filter.setCurrentIndex(max(0, self.group_filter.findData(current)))
        self.group_filter.blockSignals(False)
        if hasattr(self, "event_group"):
            selected = self.event_group.currentData(); self.event_group.blockSignals(True)
            self.event_group.clear(); self.event_group.addItem("全部", None)
            for row in self.store.groups(): self.event_group.addItem(row["name"], row["id"])
            self.event_group.setCurrentIndex(max(0, self.event_group.findData(selected)))
            self.event_group.blockSignals(False)

    def refresh(self) -> None:
        rows = self.store.competitors(self.group_filter.currentData())
        needle = self.product_search.text().strip().casefold()
        if needle:
            rows = [row for row in rows if needle in " ".join((row["alias"] or row["title"] or row["offer_id"], row["shop_name"] or "")).casefold()]
        if self.only_changed.isChecked(): rows = [row for row in rows if row["latest_change"]]
        if self.only_failed.isChecked(): rows = [row for row in rows if row["status"] in ("部分异常", "最近采集失败")]
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            snapshot = self.store.latest_snapshot(row["id"])
            name = row["alias"] or row["title"] or row["offer_id"]
            product = ProductCell(name, row["shop_name"] or "店铺未知", row["group_name"] or "未分组")
            self.table.setCellWidget(row_index, 0, product)
            values = (_prices(snapshot), _field(snapshot, "sales_raw"), _field(snapshot, "month_sales_raw"),
                      str(len(_json_field(snapshot, "visible_sku_names_json"))), row["latest_change"] or "--", status_text(row), "")
            for column, value in enumerate(values, 1):
                item = QTableWidgetItem(value); item.setData(Qt.ItemDataRole.UserRole, row["id"]); item.setToolTip(value)
                self.table.setItem(row_index, column, item)
            status = QLabel(status_text(row), objectName="statusTag", alignment=Qt.AlignmentFlag.AlignCenter)
            status.setProperty("status", status_text(row)); self.table.setCellWidget(row_index, 6, status)
            first = QTableWidgetItem(name); first.setData(Qt.ItemDataRole.UserRole, row["id"]); self.table.setItem(row_index, 0, first)
            action = QToolButton(objectName="rowMenu"); action.setText("···"); action.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            menu = QMenu(action)
            for label, slot in (("立即采集", self.collect_selected), ("查看详情", self.open_history), ("编辑", self.edit_selected),
                                ("恢复监控" if row["status"] == "暂停" else "暂停监控", self.toggle_selected), ("删除", self.delete_selected)):
                menu.addAction(label, lambda checked=False, rid=row["id"], fn=slot: self._run_row_action(rid, fn))
            action.setMenu(menu); self.table.setCellWidget(row_index, 7, action)
            self.table.setRowHeight(row_index, 72)
        self.show_latest()
        self.refresh_dashboard(); self.refresh_events()

    def refresh_dashboard(self) -> None:
        summary = self.store.today_summary()
        for label, value in zip(self.stat_values, (summary["total"], summary["success"], summary["price"], summary["sales"], summary["partial"] + summary["failed"])):
            label.setText(str(value))
        self.summary.setText(f"监控商品 {summary['total']} 今日成功 {summary['success']} 价格变化 {summary['price']} SKU变化 {summary['sku']} 销量异常 {summary['sales']} 采集异常 {summary['partial'] + summary['failed']}")
        self._fill_events(self.today_table, self.store.events(date=date.today().isoformat()), today=True)
        empty = self.today_table.rowCount() == 0; self.today_empty.setVisible(empty); self.today_table.setVisible(not empty)

    def refresh_events(self) -> None:
        rows = self.store.events(event_type=self.event_type.currentData(), group_id=self.event_group.currentData())
        start, end = self.event_date.date().toString("yyyy-MM-dd"), self.event_end.date().toString("yyyy-MM-dd")
        needle = self.event_search.text().strip().casefold()
        rows = [row for row in rows if start <= row["created_at"][:10] <= end and (not needle or needle in row["competitor_name"].casefold())]
        self._fill_events(self.events_table, rows)

    @staticmethod
    def _fill_events(table: QTableWidget, rows, *, today=False) -> None:
        table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            shown, magnitude = format_event_parts(row)
            values = ((format_time(row["created_at"]), row["competitor_name"], row["title"], shown, magnitude) if today else
                      (format_time(row["created_at"], full=True), row["competitor_name"], row["title"], shown, severity_text(row["severity"])))
            for column, value in enumerate(values):
                item = QTableWidgetItem(value); item.setData(Qt.ItemDataRole.UserRole, row["competitor_id"])
                item.setToolTip(value)
                table.setItem(index, column, item)
            table.setRowHeight(index, 54)

    def open_event_product(self, table: QTableWidget, row: int) -> None:
        competitor_id = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.tabs.setCurrentIndex(1); self.refresh()
        for index in range(self.table.rowCount()):
            if self.table.item(index, 0).data(Qt.ItemDataRole.UserRole) == competitor_id:
                self.table.selectRow(index); self.open_history(); break

    def selected_id(self):
        items = self.table.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None

    def selected_ids(self):
        return [self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole) for index in self.table.selectionModel().selectedRows()]

    def _selection_changed(self) -> None:
        count = len(self.selected_ids()); self.batch_count.setText(f"已选择 {count} 个商品"); self.batch_bar.setVisible(count > 1); self.show_latest()

    def _run_row_action(self, competitor_id: int, action) -> None:
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).data(Qt.ItemDataRole.UserRole) == competitor_id:
                self.table.clearSelection(); self.table.selectRow(row); break
        action()

    def add_competitors(self) -> None:
        dialog = CompetitorDialog(self.store, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        group_id, alias, note = dialog.values(); new_ids, duplicates, errors = [], [], []
        lines = [line.strip() for line in dialog.urls.toPlainText().splitlines() if line.strip()]
        for line in lines:
            try:
                competitor_id, created = self.store.add_competitor(line, group_id, alias if len(lines) == 1 else "", note if len(lines) == 1 else "")
                (new_ids if created else duplicates).append(competitor_id)
            except (ValueError, sqlite3.Error) as exc: errors.append(f"{line}: {exc}")
        self.refresh()
        if errors: MessageDialog("部分链接未添加", "部分链接无法添加。", self, details="\n".join(errors)).exec()
        if duplicates: MessageDialog("商品已存在", f"{len(duplicates)} 个链接已存在。", self).exec()
        if new_ids: self.start_collection(new_ids)

    def manage_groups(self) -> None:
        GroupManagerDialog(self.store, self).exec()
        self.refresh_groups(); self.refresh()

    def edit_selected(self) -> None:
        competitor_id = self.selected_id()
        if not competitor_id: return
        dialog = CompetitorDialog(self.store, self.store.competitor(competitor_id), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            group_id, alias, note = dialog.values(); self.store.update_competitor(competitor_id, alias=alias, note=note, group_id=group_id); self.refresh()

    def toggle_selected(self) -> None:
        for competitor_id in self.selected_ids():
            row = self.store.competitor(competitor_id); self.store.set_enabled(competitor_id, not bool(row["monitor_enabled"]))
        self.refresh()

    def delete_selected(self) -> None:
        competitor_ids = self.selected_ids()
        if competitor_ids and MessageDialog("删除商品", f"删除选中的 {len(competitor_ids)} 个商品及全部历史数据？", self, confirm=True).exec() == QDialog.DialogCode.Accepted:
            for competitor_id in competitor_ids: self.store.delete_competitor(competitor_id)
            self.refresh()

    def collect_all(self) -> None:
        self.start_collection([row["id"] for row in self.store.competitors(self.group_filter.currentData(), True)])

    def collect_selected(self) -> None:
        competitor_ids = self.selected_ids()
        if competitor_ids: self.start_collection(competitor_ids)

    def start_collection(self, competitor_ids: list[int]) -> None:
        if self.worker and self.worker.isRunning(): return
        competitors = [dict(self.store.competitor(item)) for item in competitor_ids if self.store.competitor(item)]
        if not competitors: MessageDialog("没有任务", "当前没有需要采集的商品。", self).exec(); return
        self.progress = CollectionProgress(len(competitors), self)
        self.run_id = self.store.start_run(len(competitors))
        self.worker = CollectionWorker(competitors, self.cdp.text().strip())
        self.progress.cancel.clicked.connect(self.worker.cancel)
        self.worker.state.connect(self.progress.set_state)
        self.worker.current.connect(lambda index, total, _id, name: (self.progress.update_progress(index - 1, total), self.progress.set_current(index, total, name)))
        self.worker.item_completed.connect(self._save_result)
        self.worker.environment_failed.connect(self._environment_failed)
        self.worker.completed.connect(self._collection_finished)
        self.worker.start(); self.progress.show()

    def _save_result(self, competitor_id, result) -> None:
        self.store.save_collection(
            competitor_id, result,
            price_threshold=float(self.settings.value("price_threshold", 5)),
            sales_threshold=int(self.settings.value("sales_threshold", 20)),
        )
        self.progress.update_progress(self.progress.bar.value() + 1, self.progress.bar.maximum())

    def _collection_finished(self, cancelled: bool, success: int, partial: int, failed: int) -> None:
        self.progress.accept(); self.refresh()
        status = "cancelled" if cancelled else "completed"
        self.store.finish_run(self.run_id, status, success, partial, failed)
        MessageDialog("采集已取消" if cancelled else "采集完成",
                      f"成功 {success}　部分异常 {partial}　失败 {failed}\n已完成的数据均已保存。", self).exec()

    def _environment_failed(self, error: str, technical_error: str) -> None:
        self.progress.accept(); self.store.finish_run(self.run_id, "environment_failed", error=technical_error or error); self.refresh()
        MessageDialog("采集环境不可用", error, self, details=technical_error, open_browser="登录状态" in error).exec()

    def show_latest(self) -> None:
        competitor_id = self.selected_id()
        snapshot = self.store.latest_snapshot(competitor_id) if competitor_id else None
        competitor = self.store.competitor(competitor_id) if competitor_id else None
        self._failure_details = self.store.latest_failure_details(competitor_id) if competitor and competitor["status"] == "最近采集失败" else None
        self.detail_button.setVisible(bool(self._failure_details and self._failure_details.get("technical_error")))
        if not snapshot:
            error = self._failure_details["error"] if self._failure_details else None
            self.detail.setText(f"采集失败：{error}" if error else ("选择商品查看最近快照" if not competitor_id else "该商品还没有成功快照"))
            return
        error = self._failure_details["error"] if self._failure_details else None
        missing = "、".join(_json_field(snapshot, "missing_fields_json")) or "无"
        suffix = f"\n最近失败：{error}" if competitor["status"] == "最近采集失败" and error else ""
        self.detail.setText(f"最近快照：{snapshot['collected_at']}　起批量：{snapshot['min_order_qty'] or '--'}　SKU：{'、'.join(_json_field(snapshot, 'visible_sku_names_json')) or '--'}\n缺失字段：{missing}{suffix}")

    def _show_failure_details(self) -> None:
        if self._failure_details:
            MessageDialog("采集失败详情", self._failure_details["error"], self,
                          details=self._failure_details.get("technical_error", "")).exec()

    def open_history(self) -> None:
        competitor_id = self.selected_id()
        if not competitor_id: return
        self.history_dialog = HistoryDialog(self.store, competitor_id, self)
        self.history_dialog.show()

    def _scheduler(self) -> TaskScheduler:
        python = Path(sys.executable)
        pythonw = python.with_name("pythonw.exe")
        return TaskScheduler(pythonw if pythonw.exists() else python, Path(__file__).parents[2] / "main.py")

    def enable_schedule(self) -> None:
        scheduled_time = self.scheduled_time.time().toString("HH:mm")
        self.settings.setValue("scheduled_time", scheduled_time)
        self.settings.setValue("catch_up", self.catch_up.isChecked())
        self.settings.setValue("notification_enabled", self.notifications.isChecked())
        self.settings.setValue("price_threshold", self.price_threshold.value())
        self.settings.setValue("sales_threshold", self.sales_threshold.value())
        try:
            self._scheduler().install(scheduled_time, self.catch_up.isChecked())
            self.schedule_status.setText(f"自动采集已启用：每天 {scheduled_time}" + ("，当天漏采会在登录时补采。" if self.catch_up.isChecked() else "。"))
        except RuntimeError as exc:
            self.schedule_status.setText("自动采集启用失败：系统未允许创建计划任务，请检查应用权限。")
            MessageDialog("自动采集启用失败", "系统未允许创建计划任务，请检查应用权限。", self, details=str(exc)).exec()

    def save_settings(self) -> None:
        self.settings.setValue("cdp_url", self.cdp.text().strip())
        self.settings.setValue("retention", self.retention.currentText())
        self.settings.setValue("schedule_enabled", self.schedule_enabled.isChecked())
        if self.schedule_enabled.isChecked(): self.enable_schedule()
        else:
            self.settings.setValue("scheduled_time", self.scheduled_time.time().toString("HH:mm"))
            self.settings.setValue("catch_up", self.catch_up.isChecked())
            self.settings.setValue("notification_enabled", self.notifications.isChecked())
            self.settings.setValue("price_threshold", self.price_threshold.value())
            self.settings.setValue("sales_threshold", self.sales_threshold.value())
            try: self.disable_schedule()
            except RuntimeError as exc: MessageDialog("自动采集停用失败", "系统未能更新计划任务，请检查应用权限。", self, details=str(exc)).exec()

    def disable_schedule(self) -> None:
        self._scheduler().remove()
        self.schedule_status.setText("自动采集已停用。")


def _field(row, name): return str(row[name] or "--") if row else "--"
def _json_field(row, name): return json.loads(row[name]) if row and row[name] else []
def _prices(row):
    values = _json_field(row, "price_raw_values_json")
    if not values: return "--"
    cleaned = [str(value).replace("￥", "¥").strip() for value in values]
    return cleaned[0] if len(cleaned) == 1 else f"{cleaned[0]} – {cleaned[-1]}"


def format_time(value, *, full=False):
    if not value or value == "--": return "--"
    value = str(value).replace("T", " ")
    return value[:16] if full else value[11:16]


def _display_value(value):
    if isinstance(value, list): return " – ".join(map(str, value)) if len(value) > 1 else (str(value[0]) if value else "--")
    return "--" if value in (None, "") else str(value)


def format_event_parts(event):
    detail = json.loads(event["detail_json"])
    before, after = _display_value(detail.get("before")), _display_value(detail.get("after"))
    shown = f"{before} → {after}" if before != "--" or after != "--" else ""
    if detail.get("items"): shown = "、".join(map(str, detail["items"]))
    magnitude = ""
    if detail.get("change_percent") is not None:
        amount = ""
        old_number = _first_number(before); new_number = _first_number(after)
        if old_number is not None and new_number is not None:
            difference = new_number - old_number; amount = f"{'+' if difference >= 0 else '-'}¥{abs(difference):g} / "
        magnitude = f"{amount}{detail['change_percent']:+.1f}%"
    elif detail.get("lower_bound_change") is not None: magnitude = f"{detail['lower_bound_change']:+d}（展示下界）"
    return shown or event["title"], magnitude or "--"


def _first_number(value):
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(match.group()) if match else None


def format_event_detail(event):
    shown, magnitude = format_event_parts(event)
    return f"{shown}　{magnitude}" if magnitude != "--" else shown


def severity_text(value): return {"error": "异常", "warning": "需关注", "important": "有变化"}.get(value, "已记录")


def status_text(row):
    return {"最近采集失败": "采集失败", "部分异常": "异常"}.get(row["status"], row["status"])


def card_widget(name="monitorCard"):
    return QFrame(objectName=name)


def metric_card(title, tone="primary"):
    card = card_widget("statCard"); card.setProperty("tone", tone)
    layout = QVBoxLayout(card); layout.setContentsMargins(18, 14, 18, 14); layout.setSpacing(2)
    value = QLabel("0", objectName="statValue"); layout.addWidget(QLabel(title, objectName="statLabel")); layout.addWidget(value)
    return card, value


def settings_card(title, rows):
    card = card_widget(); layout = QVBoxLayout(card); layout.setContentsMargins(18, 16, 18, 18); layout.addWidget(QLabel(title, objectName="cardTitle"))
    form = QFormLayout(); form.setVerticalSpacing(12)
    for label, widget in rows: form.addRow(label, widget)
    layout.addLayout(form); return card


def configure_table(table, widths, *, stretch):
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setWordWrap(False); table.setShowGrid(False); table.verticalHeader().hide()
    for column, width in enumerate(widths): table.setColumnWidth(column, width)
    table.horizontalHeader().setSectionResizeMode(stretch, QHeaderView.ResizeMode.Stretch)
