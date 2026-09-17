from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QInputDialog,
)

from services.competitor_monitor import MonitorStore, parse_offer_url
from tools.competitor_monitor.worker import CollectionWorker


class CompetitorDialog(QDialog):
    def __init__(self, store: MonitorStore, competitor=None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("编辑竞品" if competitor else "添加竞品")
        self.resize(580, 420 if not competitor else 320)
        layout = QVBoxLayout(self)
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
        layout.addLayout(form)
        actions = QHBoxLayout(); actions.addStretch()
        cancel = QPushButton("取消"); save = QPushButton("保存", objectName="primary")
        cancel.clicked.connect(self.reject); save.clicked.connect(self.accept)
        actions.addWidget(cancel); actions.addWidget(save); layout.addLayout(actions)

    def values(self):
        return self.group.currentData(), self.alias.text(), self.note.toPlainText()


class CollectionProgress(QDialog):
    def __init__(self, total: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("立即采集")
        self.setModal(True); self.resize(440, 150)
        layout = QVBoxLayout(self)
        self.label = QLabel(f"准备采集 {total} 个商品")
        self.bar = QProgressBar(); self.bar.setRange(0, total)
        self.cancel = QPushButton("取消剩余任务")
        layout.addWidget(self.label); layout.addWidget(self.bar); layout.addWidget(self.cancel, alignment=Qt.AlignmentFlag.AlignRight)


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

        self.table = QTableWidget(0, 9, objectName="previewTable")
        self.table.setHorizontalHeaderLabels(("商品", "分组", "展示价格", "页面已售", "月成交", "年成交件数", "SKU", "最近采集", "状态"))
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.show_latest)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 9): self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        for label, slot in (("采集选中", self.collect_selected), ("编辑", self.edit_selected), ("暂停/恢复", self.toggle_selected), ("删除", self.delete_selected)):
            button = QPushButton(label); button.clicked.connect(slot); actions.addWidget(button)
        actions.addStretch(); root.addLayout(actions)
        self.detail = QLabel("选择商品查看最近快照", objectName="helperText")
        self.detail.setWordWrap(True); root.addWidget(self.detail)
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
            values = [row["alias"] or row["title"] or row["offer_id"], row["group_name"] or "未分组",
                      _prices(snapshot), _field(snapshot, "sales_raw"), _field(snapshot, "month_sales_raw"),
                      _field(snapshot, "year_sales_quantity_raw"), str(len(_json_field(snapshot, "visible_sku_names_json"))),
                      row["last_attempt_at"] or "--", row["status"]]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value); item.setData(Qt.ItemDataRole.UserRole, row["id"])
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
        if errors: QMessageBox.warning(self, "部分链接未添加", "\n".join(errors))
        if duplicates: QMessageBox.information(self, "商品已存在", f"{len(duplicates)} 个链接已存在。")
        if new_ids: self.start_collection(new_ids)

    def manage_groups(self) -> None:
        names = [row["name"] for row in self.store.groups()]
        choice, ok = QInputDialog.getItem(self, "管理分组", "选择分组（选择“新建分组”可创建）", ["新建分组", *names], 0, False)
        if not ok: return
        if choice == "新建分组":
            name, ok = QInputDialog.getText(self, "新建分组", "分组名称")
            if ok:
                try: self.store.add_group(name)
                except (ValueError, sqlite3.IntegrityError) as exc: QMessageBox.warning(self, "无法新建", str(exc))
        else:
            action, ok = QInputDialog.getItem(self, "管理分组", choice, ["重命名", "删除（商品移至未分组）"], 0, False)
            if not ok: return
            group_id = next(row["id"] for row in self.store.groups() if row["name"] == choice)
            if action == "重命名":
                name, ok = QInputDialog.getText(self, "重命名分组", "新名称", text=choice)
                if ok:
                    try: self.store.rename_group(group_id, name)
                    except (ValueError, sqlite3.IntegrityError) as exc: QMessageBox.warning(self, "无法重命名", str(exc))
            elif QMessageBox.question(self, "删除分组", "商品将移动到“未分组”，继续吗？") == QMessageBox.StandardButton.Yes:
                self.store.delete_group(group_id)
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
        if competitor_id and QMessageBox.question(self, "删除商品", "删除商品及全部历史数据？") == QMessageBox.StandardButton.Yes:
            self.store.delete_competitor(competitor_id); self.refresh()

    def collect_all(self) -> None:
        self.start_collection([row["id"] for row in self.store.competitors(self.group_filter.currentData(), True)])

    def collect_selected(self) -> None:
        competitor_id = self.selected_id()
        if competitor_id: self.start_collection([competitor_id])

    def start_collection(self, competitor_ids: list[int]) -> None:
        if self.worker and self.worker.isRunning(): return
        competitors = [dict(self.store.competitor(item)) for item in competitor_ids if self.store.competitor(item)]
        if not competitors: QMessageBox.information(self, "没有任务", "当前没有需要采集的商品。"); return
        self.progress = CollectionProgress(len(competitors), self)
        self.worker = CollectionWorker(competitors, self.cdp.text().strip())
        self.progress.cancel.clicked.connect(self.worker.cancel)
        self.worker.current.connect(lambda index, total, _id, name: (self.progress.bar.setValue(index - 1), self.progress.label.setText(f"正在监控 {index} / {total}\n当前：{name}")))
        self.worker.item_completed.connect(self._save_result)
        self.worker.completed.connect(self._collection_finished)
        self.worker.start(); self.progress.show()

    def _save_result(self, competitor_id, result) -> None:
        self.store.save_collection(competitor_id, result); self.progress.bar.setValue(self.progress.bar.value() + 1)

    def _collection_finished(self, cancelled: bool) -> None:
        self.progress.accept(); self.refresh()
        QMessageBox.information(self, "采集已取消" if cancelled else "采集完成", "已完成的数据均已保存。")

    def show_latest(self) -> None:
        competitor_id = self.selected_id()
        snapshot = self.store.latest_snapshot(competitor_id) if competitor_id else None
        if not snapshot:
            error = self.store.latest_failure(competitor_id) if competitor_id else None
            self.detail.setText(f"采集失败：{error}" if error else ("选择商品查看最近快照" if not competitor_id else "该商品还没有成功快照"))
            return
        error = self.store.latest_failure(competitor_id)
        missing = "、".join(_json_field(snapshot, "missing_fields_json")) or "无"
        suffix = f"\n最近失败：{error}" if self.store.competitor(competitor_id)["status"] == "采集失败" and error else ""
        self.detail.setText(f"最近快照：{snapshot['collected_at']}　起批量：{snapshot['min_order_qty'] or '--'}　SKU：{'、'.join(_json_field(snapshot, 'visible_sku_names_json')) or '--'}\n缺失字段：{missing}{suffix}")


def _field(row, name): return str(row[name] or "--") if row else "--"
def _json_field(row, name): return json.loads(row[name]) if row and row[name] else []
def _prices(row): return " / ".join(_json_field(row, "price_raw_values_json")) or "--"
