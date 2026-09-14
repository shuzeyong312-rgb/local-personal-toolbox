from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.icons import icon
from components.controls import AppComboBox, AppSpinBox
from components.dialogs import TaskDialog
from services.file_rename import RenamePlan, build_rename_plan, find_conflicts
from tools.rename.worker import RenameWorker


class RenamePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[Path] = []
        self.plans: list[RenamePlan] = []
        self.worker: RenameWorker | None = None
        self.task_dialog: TaskDialog | None = None
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "rename")
        self._loading = False
        self._build_ui()
        self._restore_settings()
        self._connect_controls()
        self.refresh_preview()

    def _build_ui(self) -> None:
        self.setObjectName("page")
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 14, 28, 20)
        root.setSpacing(6)
        root.addWidget(QLabel("批量重命名", objectName="pageTitle"))
        root.addWidget(QLabel("按文件时间稳定排序并统一编号，执行前可完整预览。", objectName="pageSubtitle"))
        root.addSpacing(8)
        content = QHBoxLayout()
        content.setSpacing(14)
        content.addWidget(self._preview_panel(), 3)
        content.addWidget(self._settings_panel(), 2)
        root.addLayout(content, 1)

    @staticmethod
    def _card(title: str) -> tuple[QWidget, QVBoxLayout]:
        card = QWidget(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addWidget(QLabel(title, objectName="cardTitle"))
        return card, layout

    @staticmethod
    def _field(label: str, widget: QWidget) -> QWidget:
        field = QWidget(objectName="field")
        layout = QVBoxLayout(field)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(QLabel(label, objectName="fieldLabel"))
        layout.addWidget(widget)
        return field

    def _preview_panel(self) -> QWidget:
        card, layout = self._card("重命名预览")
        self.preview_card = card
        self.table = QTableWidget(0, 3, objectName="previewTable")
        self.table.setHorizontalHeaderLabels(["原文件名", "时间", "新文件名"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        actions = QHBoxLayout()
        add = QPushButton("添加文件", objectName="primary")
        add.setIcon(icon("plus", "#FFFFFF"))
        folder = QPushButton("添加文件夹")
        folder.setIcon(icon("folder"))
        remove = QPushButton("移除选中", objectName="ghost")
        clear = QPushButton("清空", objectName="ghost")
        add.clicked.connect(self.choose_files)
        folder.clicked.connect(self.choose_folder)
        remove.clicked.connect(self.remove_selected)
        clear.clicked.connect(self.clear_files)
        actions.addWidget(add)
        actions.addWidget(folder)
        actions.addWidget(remove)
        actions.addStretch()
        self.count_label = QLabel("共 0 个文件", objectName="countLabel")
        actions.addWidget(self.count_label)
        actions.addWidget(clear)
        layout.addLayout(actions)
        return card

    def _settings_panel(self) -> QWidget:
        self.settings_card, layout = self._card("命名设置")
        self.sort_by = AppComboBox()
        for label, value in (("修改时间：从早到晚", "mtime_asc"), ("修改时间：从晚到早", "mtime_desc"),
                             ("创建时间：从早到晚", "ctime_asc"), ("文件名排序", "name")):
            self.sort_by.addItem(label, value)
        layout.addWidget(self._field("排序方式", self.sort_by))
        self.prefix = QLineEdit("详情页_")
        self.prefix.setMaxLength(120)
        layout.addWidget(self._field("文件名前缀", self.prefix))
        self.start_number = AppSpinBox()
        self.start_number.setRange(0, 999999)
        self.start_number.setValue(1)
        self.digits = AppComboBox()
        self.digits.addItem("自动", None)
        self.digits.addItem("2 位", 2)
        self.digits.addItem("3 位", 3)
        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.addWidget(self._field("起始序号", self.start_number), 0, 0)
        grid.addWidget(self._field("序号位数", self.digits), 0, 1)
        layout.addLayout(grid)
        self.rule_hint = QLabel("扩展名将自动保留；相同时间按原文件名排序。", objectName="helperText")
        self.rule_hint.setWordWrap(True)
        layout.addWidget(self.rule_hint)
        layout.addStretch()
        self.error_label = QLabel("", objectName="fieldError")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        self.start_hint = QLabel("请先添加文件", objectName="helperText")
        layout.addWidget(self.start_hint)
        self.start_button = QPushButton("开始重命名", objectName="startButton")
        self.start_button.clicked.connect(self.start_processing)
        layout.addWidget(self.start_button)
        return self.settings_card

    def _connect_controls(self) -> None:
        for signal in (self.sort_by.currentIndexChanged, self.prefix.textChanged,
                       self.start_number.valueChanged, self.digits.currentIndexChanged):
            signal.connect(self.refresh_preview)
            signal.connect(self._save_settings)

    def choose_files(self) -> None:
        names, _ = QFileDialog.getOpenFileNames(self, "选择文件", self._source_dir(), "所有文件 (*)")
        if names:
            self.add_files([Path(name) for name in names])

    def choose_folder(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择文件夹", self._source_dir())
        if name:
            self.add_files(sorted(path for path in Path(name).iterdir() if path.is_file()))

    def _source_dir(self) -> str:
        path = Path(self.settings.value("source_dir", "", type=str))
        return str(path) if path.is_dir() else str(Path.home())

    def add_files(self, paths: list[Path]) -> None:
        files = [path.resolve() for path in paths if path.is_file()]
        if not files:
            return
        expected_parent = self.sources[0].parent if self.sources else files[0].parent
        if any(path.parent != expected_parent for path in files):
            self.error_label.setText("请选择同一文件夹中的文件")
            return
        known = {str(path).casefold() for path in self.sources}
        for path in files:
            if str(path).casefold() not in known:
                self.sources.append(path)
                known.add(str(path).casefold())
        self.settings.setValue("source_dir", str(expected_parent))
        self.settings.sync()
        self.refresh_preview()

    def remove_selected(self) -> None:
        selected = {index.row() for index in self.table.selectionModel().selectedRows()}
        remove_paths = {self.plans[row].source for row in selected if row < len(self.plans)}
        self.sources = [path for path in self.sources if path not in remove_paths]
        self.refresh_preview()

    def clear_files(self) -> None:
        self.sources.clear()
        self.refresh_preview()

    def refresh_preview(self, *_args) -> None:
        error = ""
        try:
            self.plans = build_rename_plan(self.sources, self.prefix.text(), self.start_number.value(),
                                           self.digits.currentData(), self.sort_by.currentData())
            conflicts = find_conflicts(self.plans)
            if conflicts:
                error = "；".join(conflicts[:3])
        except ValueError as exc:
            self.plans = []
            error = str(exc)
        self.table.setRowCount(len(self.plans))
        for row, plan in enumerate(self.plans):
            values = (plan.source.name, datetime.fromtimestamp(plan.timestamp).strftime("%Y-%m-%d %H:%M:%S"), plan.destination.name)
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.count_label.setText(f"共 {len(self.sources)} 个文件")
        self.error_label.setText(error)
        self.error_label.setVisible(bool(error))
        ready = bool(self.plans and not error and self.worker is None)
        self.start_button.setEnabled(ready)
        self.start_button.setText(f"重命名 {len(self.plans)} 个文件" if self.plans else "开始重命名")
        self.start_hint.setText("正在处理，请稍候" if self.worker else "请先添加文件" if not self.sources else "请解决文件名冲突" if error else "预览无误后即可开始")

    def _save_settings(self, *_args) -> None:
        if self._loading:
            return
        for key, value in (("sort_by", self.sort_by.currentData()), ("prefix", self.prefix.text()),
                           ("start", self.start_number.value()), ("digits", self.digits.currentIndex())):
            self.settings.setValue(key, value)
        self.settings.sync()

    def _restore_settings(self) -> None:
        self._loading = True
        try:
            index = self.sort_by.findData(self.settings.value("sort_by", "mtime_asc", type=str))
            self.sort_by.setCurrentIndex(index if index >= 0 else 0)
            self.prefix.setText(self.settings.value("prefix", "详情页_", type=str))
            try:
                self.start_number.setValue(int(self.settings.value("start", 1)))
                self.digits.setCurrentIndex(min(max(int(self.settings.value("digits", 0)), 0), 2))
            except (TypeError, ValueError):
                self.start_number.setValue(1)
                self.digits.setCurrentIndex(0)
        finally:
            self._loading = False

    def start_processing(self) -> None:
        self.refresh_preview()
        if self.worker or not self.start_button.isEnabled():
            return
        folder = self.plans[0].source.parent
        self.task_dialog = TaskDialog(len(self.plans), folder, self, "正在重命名文件")
        self.worker = RenameWorker(self.plans.copy())
        self.worker.progress.connect(lambda done, total, success, failed: self.task_dialog and self.task_dialog.update_progress(done, total, success, failed))
        self.worker.completed.connect(self._on_completed)
        self.worker.finished.connect(self._worker_finished)
        self.settings_card.setEnabled(False)
        self.preview_card.setEnabled(False)
        self.worker.start()
        self.task_dialog.open()

    def _on_completed(self, success: int, failed: int, failures: list[str]) -> None:
        if self.task_dialog:
            self.task_dialog.show_result(success, failed, failures, "重命名完成")

    def _worker_finished(self) -> None:
        self.worker = None
        self.settings_card.setEnabled(True)
        self.preview_card.setEnabled(True)
        self.sources = [plan.destination for plan in self.plans if plan.destination.exists()]
        self.refresh_preview()

    def stop_worker(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.wait()
