from pathlib import Path

from PIL import Image, ImageOps
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.icons import icon
from components.controls import AppComboBox, AppSpinBox
from components.dialogs import TaskDialog
from components.image_drop_list import ImageDropList
from tools.compression.worker import CompressionWorker
from utils.image_files import images_in_folder


def format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return ""


class CompressionPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[Path] = []
        self.worker: CompressionWorker | None = None
        self.task_dialog: TaskDialog | None = None
        self.output_dir: Path | None = None
        self._build_ui()
        self._update_state()

    @staticmethod
    def _card(title: str) -> tuple[QWidget, QVBoxLayout]:
        card = QWidget(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addWidget(QLabel(title, objectName="cardTitle"))
        return card, layout

    def _build_ui(self) -> None:
        self.setObjectName("page")
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 14, 28, 20)
        root.setSpacing(6)
        root.addWidget(QLabel("批量图片压缩", objectName="pageTitle"))
        root.addWidget(QLabel("减小图片体积，尽量保持清晰度；默认不改变尺寸和格式。", objectName="pageSubtitle"))
        root.addSpacing(8)

        files_card, files = self._card("图片文件")
        self.files_card = files_card
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
        self.drop_list = ImageDropList()
        self.drop_list.setMaximumHeight(72)
        self.drop_list.filesDropped.connect(self.add_files)
        files.addWidget(self.drop_list)
        self.table = QTableWidget(0, 7, objectName="previewTable")
        self.table.setHorizontalHeaderLabels(["文件名", "格式", "尺寸", "压缩前", "压缩后", "减少", "状态"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 7):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        files.addWidget(self.table, 1)
        root.addWidget(files_card, 1)

        settings_card, settings = self._card("压缩设置")
        self.settings_card = settings_card
        row = QHBoxLayout()
        row.addWidget(QLabel("图片质量", objectName="fieldLabel"))
        self.quality_mode = AppComboBox()
        for text, quality in (("高质量（90）", 90), ("推荐（80）", 80), ("高压缩（65）", 65), ("自定义", None)):
            self.quality_mode.addItem(text, quality)
        self.quality_mode.setCurrentIndex(1)
        row.addWidget(self.quality_mode, 1)
        self.custom_quality = AppSpinBox()
        self.custom_quality.setRange(1, 100)
        self.custom_quality.setValue(80)
        self.custom_quality.setSuffix(" %")
        self.custom_quality.hide()
        row.addWidget(self.custom_quality)
        settings.addLayout(row)
        settings.addWidget(QLabel("PNG 使用无损优化，质量数值仅作用于 JPG/JPEG 和 WebP。", objectName="helperText"))
        output_row = QHBoxLayout()
        self.output_button = QPushButton("输出到：原目录 / 压缩结果", objectName="outputButton")
        self.output_button.setIcon(icon("folder-open"))
        self.output_button.clicked.connect(self.choose_output)
        default_output = QPushButton("使用默认位置")
        default_output.clicked.connect(self.use_default_output)
        output_row.addWidget(self.output_button, 1)
        output_row.addWidget(default_output)
        settings.addLayout(output_row)
        self.start_button = QPushButton("开始批量压缩", objectName="startButton")
        self.start_button.clicked.connect(self.start_processing)
        settings.addWidget(self.start_button)
        root.addWidget(settings_card)
        self.quality_mode.currentIndexChanged.connect(self._quality_changed)

    def choose_files(self) -> None:
        names, _ = QFileDialog.getOpenFileNames(self, "选择图片", str(Path.home()), "图片 (*.jpg *.jpeg *.png *.webp)")
        self.add_files([Path(name) for name in names])

    def choose_folder(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择图片文件夹", str(Path.home()))
        if name:
            self.add_files(images_in_folder(Path(name)))

    def choose_output(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择输出目录", str(self.output_dir or Path.home()))
        if name:
            self.output_dir = Path(name).resolve()
            self.output_button.setText(f"输出到：{self.output_dir.name}")
            self.output_button.setToolTip(str(self.output_dir))

    def use_default_output(self) -> None:
        self.output_dir = None
        self.output_button.setText("输出到：原目录 / 压缩结果")
        self.output_button.setToolTip("")

    def add_files(self, paths: list[Path]) -> None:
        known = {str(path).lower() for path in self.sources}
        for path in paths:
            source = path.resolve()
            if not source.is_file() or source.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"} or str(source).lower() in known:
                continue
            self.sources.append(source)
            known.add(str(source).lower())
            row = self.table.rowCount()
            self.table.insertRow(row)
            try:
                with Image.open(source) as image:
                    width, height = ImageOps.exif_transpose(image).size
                    image_format = image.format or source.suffix[1:].upper()
            except Exception:
                width = height = 0
                image_format = source.suffix[1:].upper()
            values = (source.name, image_format, f"{width}×{height}" if width else "无法读取", format_size(source.stat().st_size), "—", "—", "待处理")
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

    def _quality_changed(self) -> None:
        self.custom_quality.setVisible(self.quality_mode.currentData() is None)

    def quality(self) -> int:
        return self.custom_quality.value() if self.quality_mode.currentData() is None else self.quality_mode.currentData()

    def _update_state(self) -> None:
        count = len(self.sources)
        self.count_label.setText(f"共 {count} 张")
        self.drop_list.setVisible(not count)
        self.start_button.setText(f"开始压缩 {count} 张图片" if count else "开始批量压缩")
        self.start_button.setEnabled(bool(count and self.worker is None))

    def _row_for(self, source: Path) -> int:
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).data(Qt.ItemDataRole.UserRole) == str(source):
                return row
        return -1

    def _item_completed(self, result) -> None:
        row = self._row_for(result.source)
        if row < 0:
            return
        self.table.item(row, 4).setText(format_size(result.compressed_size) if result.destination else "—")
        reduction = 100 * (result.original_size - result.compressed_size) / result.original_size if result.original_size else 0
        self.table.item(row, 5).setText(f"{reduction:.1f}%" if result.destination else "—")
        self.table.item(row, 6).setText(result.status)

    def _item_failed(self, source: Path, message: str) -> None:
        row = self._row_for(source)
        if row >= 0:
            self.table.item(row, 6).setText("压缩失败")
            self.table.item(row, 6).setToolTip(message)

    def start_processing(self) -> None:
        if self.worker or not self.sources:
            return
        dialog_output = self.output_dir or self.sources[0].parent / "压缩结果"
        self.task_dialog = TaskDialog(len(self.sources), dialog_output, self, "正在压缩图片", clear_task_inputs=self.clear_files)
        self.worker = CompressionWorker(self.sources.copy(), self.quality(), self.output_dir)
        self.worker.item_completed.connect(self._item_completed)
        self.worker.item_failed.connect(self._item_failed)
        self.worker.current.connect(lambda name: self.task_dialog and self.task_dialog.set_current(name))
        self.worker.progress.connect(self._progress)
        self.worker.completed.connect(self._completed)
        self.worker.finished.connect(self._worker_finished)
        self.settings_card.setEnabled(False)
        self.files_card.setEnabled(False)
        self._update_state()
        self.worker.start()
        self.task_dialog.open()

    def _progress(self, done: int, total: int, processed: int, failed: int, current: str) -> None:
        if self.task_dialog:
            self.task_dialog.update_progress(done, total, processed, failed)
            self.task_dialog.set_current(current)

    def _completed(self, success: int, skipped: int, failed: int, before: int, after: int, failures: list[str]) -> None:
        if not self.task_dialog:
            return
        self.task_dialog.show_result(success, failed, failures, "压缩完成")
        self.task_dialog.success_label.setText(f"成功 {success} 张 · 无需压缩 {skipped} 张")
        saved = before - after
        rate = saved / before * 100 if before else 0
        self.task_dialog.statistics.setText(
            f"压缩前：{format_size(before)}    压缩后：{format_size(after)}\n节省：{format_size(saved)}    压缩率：{rate:.1f}%"
        )
        self.task_dialog.statistics.show()

    def _worker_finished(self) -> None:
        if self.task_dialog and self.task_dialog.processing:
            self.task_dialog.show_result(0, len(self.sources), ["任务异常结束"], "压缩完成", completed=False)
        self.worker = None
        self.settings_card.setEnabled(True)
        self.files_card.setEnabled(True)
        self._update_state()

    def stop_worker(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()
