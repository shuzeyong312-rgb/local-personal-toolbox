import os
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.icons import icon
from components.controls import AppComboBox, AppSpinBox
from components.dialogs import TaskDialog
from components.image_drop_list import ImageDropList
from services.image_conversion import ConversionOptions
from tools.conversion.worker import ConversionWorker

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return ""


class ConversionPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[Path] = []
        self.worker: ConversionWorker | None = None
        self.task_dialog: TaskDialog | None = None
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "conversion")
        self._build_ui()
        self._restore_settings()
        self._connect_settings()
        self._update_fields()
        self._update_state()

    @staticmethod
    def _card(title: str) -> tuple[QWidget, QVBoxLayout]:
        card = QWidget(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        layout.addWidget(QLabel(title, objectName="cardTitle"))
        return card, layout

    def _build_ui(self) -> None:
        self.setObjectName("page")
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 14, 28, 20)
        root.setSpacing(6)
        root.addWidget(QLabel("图片格式转换", objectName="pageTitle"))
        root.addWidget(QLabel("批量转换图片格式，不改变尺寸、不覆盖原图。", objectName="pageSubtitle"))
        root.addSpacing(8)

        self.files_card, files = self._card("图片文件")
        actions = QHBoxLayout()
        add = QPushButton("添加图片", objectName="primary")
        add.setIcon(icon("plus", "#FFFFFF"))
        folder = QPushButton("添加文件夹")
        folder.setIcon(icon("folder"))
        clear = QPushButton("清空全部", objectName="ghost")
        add.clicked.connect(self.choose_files)
        folder.clicked.connect(self.choose_folder)
        clear.clicked.connect(self.clear_files)
        actions.addWidget(add)
        actions.addWidget(folder)
        actions.addStretch()
        self.count_label = QLabel(objectName="countLabel")
        actions.addWidget(self.count_label)
        actions.addWidget(clear)
        files.addLayout(actions)
        self.drop_list = ImageDropList(EXTENSIONS)
        self.drop_list.setToolTip("可将 JPG、JPEG、PNG、WEBP、BMP 图片拖到这里")
        self.drop_list.filesDropped.connect(self.add_files)
        self.drop_list.setMaximumHeight(70)
        files.addWidget(self.drop_list)
        self.table = QTableWidget(0, 5, objectName="previewTable")
        self.table.setHorizontalHeaderLabels(["文件名", "格式", "尺寸", "文件大小", "状态"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 5):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        files.addWidget(self.table, 1)
        root.addWidget(self.files_card, 1)

        self.settings_card, settings = self._card("转换设置")
        first = QHBoxLayout()
        first.addWidget(QLabel("目标格式", objectName="fieldLabel"))
        self.target_format = AppComboBox()
        for text, value in (("PNG", "png"), ("JPG", "jpg"), ("WebP", "webp"), ("BMP", "bmp")):
            self.target_format.addItem(text, value)
        first.addWidget(self.target_format)
        self.quality_label = QLabel("图片质量", objectName="fieldLabel")
        first.addWidget(self.quality_label)
        self.jpg_quality = AppSpinBox()
        self.jpg_quality.setRange(1, 100)
        self.jpg_quality.setValue(90)
        first.addWidget(self.jpg_quality)
        self.webp_quality = AppSpinBox()
        self.webp_quality.setRange(1, 100)
        self.webp_quality.setValue(90)
        first.addWidget(self.webp_quality)
        self.webp_mode = AppComboBox()
        self.webp_mode.addItem("高质量压缩", False)
        self.webp_mode.addItem("无损模式", True)
        first.addWidget(self.webp_mode)
        settings.addLayout(first)

        second = QHBoxLayout()
        self.background_label = QLabel("透明区域背景", objectName="fieldLabel")
        second.addWidget(self.background_label)
        self.background = AppComboBox()
        self.background.addItem("白色", "#ffffff")
        self.background.addItem("黑色", "#000000")
        self.background.addItem("自定义颜色", "custom")
        second.addWidget(self.background)
        self.color_button = QPushButton("#FFFFFF")
        self.color_button.clicked.connect(self.choose_color)
        second.addWidget(self.color_button)
        second.addWidget(QLabel("前缀", objectName="fieldLabel"))
        self.prefix = QLineEdit()
        second.addWidget(self.prefix)
        second.addWidget(QLabel("后缀", objectName="fieldLabel"))
        self.suffix = QLineEdit()
        second.addWidget(self.suffix)
        settings.addLayout(second)

        third = QHBoxLayout()
        third.addWidget(QLabel("同名文件", objectName="fieldLabel"))
        self.collision = AppComboBox()
        for text, value in (("自动重命名", "rename"), ("覆盖文件", "overwrite"), ("跳过文件", "skip")):
            self.collision.addItem(text, value)
        third.addWidget(self.collision)
        self.output_mode = AppComboBox()
        self.output_mode.addItem("指定输出目录", "specified")
        self.output_mode.addItem("原文件所在目录", "source")
        third.addWidget(self.output_mode)
        self.output_edit = QLineEdit()
        third.addWidget(self.output_edit, 1)
        self.output_button = QPushButton("选择目录")
        self.output_button.clicked.connect(self.choose_output)
        third.addWidget(self.output_button)
        settings.addLayout(third)
        self.output_error = QLabel(objectName="fieldError")
        settings.addWidget(self.output_error)
        settings.addWidget(QLabel("格式转换不能恢复源图片已损失的画质；转换为 JPG 会丢失透明通道。", objectName="helperText"))
        self.start_button = QPushButton("开始转换", objectName="startButton")
        self.start_button.clicked.connect(self.start_processing)
        settings.addWidget(self.start_button)
        root.addWidget(self.settings_card)

    def _connect_settings(self) -> None:
        self.target_format.currentIndexChanged.connect(self._update_fields)
        self.background.currentIndexChanged.connect(self._update_fields)
        self.output_mode.currentIndexChanged.connect(self._update_fields)
        for control in (self.target_format, self.jpg_quality, self.webp_quality, self.webp_mode, self.background, self.prefix, self.suffix, self.collision, self.output_mode, self.output_edit):
            signal = getattr(control, "textChanged", None) or getattr(control, "valueChanged", None) or control.currentIndexChanged
            signal.connect(self._save_settings)
        self.output_edit.textChanged.connect(self._update_state)

    def _restore_settings(self) -> None:
        def select(box: AppComboBox, key: str, default: str) -> None:
            index = box.findData(self.settings.value(key, default))
            box.setCurrentIndex(index if index >= 0 else box.findData(default))
        select(self.target_format, "target_format", "png")
        self.jpg_quality.setValue(max(1, min(100, self.settings.value("jpg_quality", 90, int))))
        self.webp_quality.setValue(max(1, min(100, self.settings.value("webp_quality", 90, int))))
        select(self.webp_mode, "webp_lossless", False)
        color = self.settings.value("background_color", "#ffffff")
        index = self.background.findData(color)
        if index < 0:
            index = self.background.findData("custom")
        self.background.setCurrentIndex(index)
        self.color_button.setText(str(color).upper())
        self.prefix.setText(self.settings.value("prefix", ""))
        self.suffix.setText(self.settings.value("suffix", ""))
        select(self.collision, "collision", "rename")
        select(self.output_mode, "output_mode", "specified")
        self.output_edit.setText(self.settings.value("output_dir", str(Path.cwd() / "output")))

    def _save_settings(self, *_args) -> None:
        self.settings.setValue("target_format", self.target_format.currentData())
        self.settings.setValue("jpg_quality", self.jpg_quality.value())
        self.settings.setValue("webp_quality", self.webp_quality.value())
        self.settings.setValue("webp_lossless", self.webp_mode.currentData())
        self.settings.setValue("background_color", self.background_color())
        self.settings.setValue("prefix", self.prefix.text())
        self.settings.setValue("suffix", self.suffix.text())
        self.settings.setValue("collision", self.collision.currentData())
        self.settings.setValue("output_mode", self.output_mode.currentData())
        self.settings.setValue("output_dir", self.output_edit.text())
        self._update_state()

    def background_color(self) -> str:
        return self.color_button.text().lower() if self.background.currentData() == "custom" else self.background.currentData()

    def choose_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.background_color()), self, "选择透明区域背景色")
        if color.isValid():
            self.color_button.setText(color.name().upper())
            self.background.setCurrentIndex(self.background.findData("custom"))
            self._save_settings()

    def _update_fields(self, *_args) -> None:
        target = self.target_format.currentData()
        self.quality_label.setVisible(target in {"jpg", "webp"})
        self.jpg_quality.setVisible(target == "jpg")
        self.webp_quality.setVisible(target == "webp")
        self.webp_mode.setVisible(target == "webp")
        self.background_label.setVisible(target == "jpg")
        self.background.setVisible(target == "jpg")
        self.color_button.setVisible(target == "jpg" and self.background.currentData() == "custom")
        specified = self.output_mode.currentData() == "specified"
        self.output_edit.setVisible(specified)
        self.output_button.setVisible(specified)
        self._update_state()

    def choose_files(self) -> None:
        names, _ = QFileDialog.getOpenFileNames(self, "选择图片", str(Path.home()), "图片 (*.jpg *.jpeg *.png *.webp *.bmp)")
        self.add_files([Path(name) for name in names])

    def choose_folder(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择图片文件夹", str(Path.home()))
        if name:
            self.add_files(sorted(path for path in Path(name).rglob("*") if path.is_file() and path.suffix.lower() in EXTENSIONS))

    def choose_output(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_edit.text() or str(Path.home()))
        if name:
            self.output_edit.setText(str(Path(name).resolve()))

    def add_files(self, paths: list[Path]) -> None:
        known = {str(path).lower() for path in self.sources}
        for path in paths:
            source = path.resolve()
            if not source.is_file() or source.suffix.lower() not in EXTENSIONS or str(source).lower() in known:
                continue
            self.sources.append(source)
            known.add(str(source).lower())
            try:
                with Image.open(source) as image:
                    image.load()
                    values = (source.name, image.format or source.suffix[1:].upper(), f"{image.width}×{image.height}", format_size(source.stat().st_size), "待处理")
            except Exception:
                values = (source.name, source.suffix[1:].upper(), "无法读取", format_size(source.stat().st_size), "待处理")
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, str(source))
                self.table.setItem(row, column, item)
        self._update_state()

    def clear_files(self) -> None:
        self.sources.clear()
        self.table.setRowCount(0)
        self._update_state()

    def _output_valid(self) -> bool:
        if self.output_mode.currentData() == "source":
            self.output_error.clear()
            return True
        text = self.output_edit.text().strip()
        if not text:
            self.output_error.setText("请选择输出目录")
            return False
        path = Path(text)
        if path.exists() and not path.is_dir():
            self.output_error.setText("输出路径不能是文件")
            return False
        parent = path if path.exists() else next((p for p in path.parents if p.exists()), None)
        if parent is None or not os.access(parent, os.W_OK):
            self.output_error.setText("输出目录不可写")
            return False
        self.output_error.clear()
        return True

    def _update_state(self, *_args) -> None:
        count = len(self.sources)
        self.count_label.setText(f"共 {count} 张")
        self.drop_list.setVisible(not count)
        self.start_button.setText(f"开始转换 {count} 张图片" if count else "开始转换")
        valid = self._output_valid()
        if valid:
            try:
                self.options()
            except ValueError as exc:
                self.output_error.setText(str(exc))
                valid = False
        self.start_button.setEnabled(bool(count and self.worker is None and valid))

    def options(self) -> ConversionOptions:
        target = self.target_format.currentData()
        return ConversionOptions(target, self.jpg_quality.value(), self.webp_quality.value(), self.webp_mode.currentData(), self.background_color(), self.prefix.text(), self.suffix.text(), self.collision.currentData())

    def start_processing(self) -> None:
        if self.worker or not self.sources or not self._output_valid():
            return
        output = Path(self.output_edit.text()).resolve() if self.output_mode.currentData() == "specified" else None
        dialog_output = output or self.sources[0].parent
        self.task_dialog = TaskDialog(len(self.sources), dialog_output, self, "图片格式转换", cancellable=True, clear_task_inputs=self.clear_files)
        self.worker = ConversionWorker(self.sources.copy(), output, self.options())
        self.task_dialog.cancel_requested.connect(self.worker.requestInterruption)
        self.worker.current.connect(lambda name: self.task_dialog and self.task_dialog.set_current(name))
        self.worker.progress.connect(self._progress)
        self.worker.completed.connect(self._completed)
        self.worker.finished.connect(self._worker_finished)
        self.files_card.setEnabled(False)
        self.settings_card.setEnabled(False)
        self._update_state()
        self.worker.start()
        self.task_dialog.open()

    def _progress(self, done: int, total: int, success: int, failed: int, current: str) -> None:
        if self.task_dialog:
            self.task_dialog.update_progress(done, total, success, failed)
            self.task_dialog.set_current(current)

    def _completed(self, success: int, skipped: int, failed: int, failures: list[str], cancelled: bool) -> None:
        if self.task_dialog:
            title = "任务已取消" if cancelled else "转换完成"
            self.task_dialog.show_result(success, failed, failures, title, completed=not cancelled)
            if skipped:
                self.task_dialog.success_label.setText(f"成功 {success} 张 · 跳过 {skipped} 张")

    def _worker_finished(self) -> None:
        if self.task_dialog and self.task_dialog.processing:
            self.task_dialog.show_result(0, len(self.sources), ["任务异常结束"], "转换完成", completed=False)
        self.worker = None
        self.files_card.setEnabled(True)
        self.settings_card.setEnabled(True)
        self._update_state()

    def stop_worker(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()
