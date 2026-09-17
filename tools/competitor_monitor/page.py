from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QPlainTextEdit, QProgressBar, QPushButton, QStackedLayout, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from components.dialogs import BaseDialog
from services.competitor_monitor import ChromeEnvironment, MonitorStore
from tools.competitor_monitor.worker import CollectionWorker


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
        self.layout.addLayout(actions)

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
        actions.addWidget(cancel); actions.addWidget(save); self.layout.addLayout(actions)


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
        actions.addWidget(cancel); actions.addWidget(save); self.layout.addLayout(actions)

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
        self.layout.addLayout(actions); self.refresh()

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


class CompetitorMonitorPage(QWidget):
    def __init__(self, db_path: Path | str = Path("data/competitor_monitor.db")) -> None:
        super().__init__(objectName="page")
        self.store = MonitorStore(db_path)
        self.settings = QSettings("LocalToolbox", "competitor_monitor")
        self.worker = None
        root = QVBoxLayout(self); root.setContentsMargins(28, 18, 28, 24); root.setSpacing(14)
        root.addWidget(QLabel("1688竞品监控", objectName="pageTitle"))
        root.addWidget(QLabel("添加竞品并手动记录公开页面快照", objectName="pageSubtitle"))

        toolbar = QHBoxLayout()
        add = QPushButton("添加竞品", objectName="primary"); add.clicked.connect(self.add_competitors)
        collect = QPushButton("立即采集"); collect.clicked.connect(self.collect_all)
        self.group_filter = QComboBox(); self.group_filter.currentIndexChanged.connect(self.refresh)
        manage = QPushButton("管理分组"); manage.clicked.connect(self.manage_groups)
        self.cdp = QLineEdit(str(self.settings.value("cdp_url", "http://127.0.0.1:9222")))
        self.cdp.setMaximumWidth(220); self.cdp.editingFinished.connect(lambda: self.settings.setValue("cdp_url", self.cdp.text().strip()))
        for widget in (add, collect, QLabel("分组"), self.group_filter, manage): toolbar.addWidget(widget)
        toolbar.addStretch(); toolbar.addWidget(QLabel("Chrome调试地址")); toolbar.addWidget(self.cdp)
        root.addLayout(toolbar)

        self.table = QTableWidget(0, 10, objectName="previewTable")
        self.table.setHorizontalHeaderLabels(("商品", "店铺", "分组", "展示价格", "页面已售", "月成交", "年成交件数", "SKU", "最近采集", "状态"))
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.show_latest)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 150)
        for column in range(2, 10): self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        for label, slot in (("采集选中", self.collect_selected), ("编辑", self.edit_selected), ("暂停/恢复", self.toggle_selected), ("删除", self.delete_selected)):
            button = QPushButton(label); button.clicked.connect(slot); actions.addWidget(button)
        actions.addStretch(); root.addLayout(actions)
        self.detail = QLabel("选择商品查看最近快照", objectName="helperText")
        self.detail.setWordWrap(True); root.addWidget(self.detail)
        self.detail_button = QPushButton("查看详情")
        self.detail_button.clicked.connect(self._show_failure_details); self.detail_button.hide()
        root.addWidget(self.detail_button, alignment=Qt.AlignmentFlag.AlignLeft)
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

    def refresh(self) -> None:
        rows = self.store.competitors(self.group_filter.currentData())
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            snapshot = self.store.latest_snapshot(row["id"])
            values = [row["alias"] or row["title"] or row["offer_id"], row["shop_name"] or "--", row["group_name"] or "未分组",
                      _prices(snapshot), _field(snapshot, "sales_raw"), _field(snapshot, "month_sales_raw"),
                      _field(snapshot, "year_sales_quantity_raw"), str(len(_json_field(snapshot, "visible_sku_names_json"))),
                      row["last_attempt_at"] or "--", row["status"]]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value); item.setData(Qt.ItemDataRole.UserRole, row["id"])
                if column in (0, 1): item.setToolTip(value)
                self.table.setItem(row_index, column, item)
        self.show_latest()

    def selected_id(self):
        items = self.table.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None

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
        competitor_id = self.selected_id()
        if competitor_id:
            row = self.store.competitor(competitor_id); self.store.set_enabled(competitor_id, not bool(row["monitor_enabled"])); self.refresh()

    def delete_selected(self) -> None:
        competitor_id = self.selected_id()
        if competitor_id and MessageDialog("删除商品", "删除商品及全部历史数据？", self, confirm=True).exec() == QDialog.DialogCode.Accepted:
            self.store.delete_competitor(competitor_id); self.refresh()

    def collect_all(self) -> None:
        self.start_collection([row["id"] for row in self.store.competitors(self.group_filter.currentData(), True)])

    def collect_selected(self) -> None:
        competitor_id = self.selected_id()
        if competitor_id: self.start_collection([competitor_id])

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
        self.store.save_collection(competitor_id, result); self.progress.update_progress(self.progress.bar.value() + 1, self.progress.bar.maximum())

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


def _field(row, name): return str(row[name] or "--") if row else "--"
def _json_field(row, name): return json.loads(row[name]) if row and row[name] else []
def _prices(row): return " / ".join(_json_field(row, "price_raw_values_json")) or "--"
