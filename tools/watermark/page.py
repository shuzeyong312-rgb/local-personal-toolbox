from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSlider,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from components.image_drop_list import ImageDropList
from components.preview_label import PreviewLabel
from services.image_processing import WatermarkOptions, render_watermark
from tools.watermark.worker import WatermarkWorker
from utils.image_files import images_in_folder
from utils.system import open_folder


class WatermarkPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[Path] = []
        self.output_dir = Path.cwd() / "output"
        self.worker: WatermarkWorker | None = None
        self.preview_timer = QTimer(self)
        self.preview_timer.setInterval(120)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        self._build_ui()
        self._connect_preview_controls()

    def _build_ui(self) -> None:
        self.setObjectName("page")
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 24, 30, 22)
        root.setSpacing(6)
        root.addWidget(QLabel("图片工具  /  批量打水印", objectName="pageEyebrow"))
        title = QLabel("批量打水印", objectName="pageTitle")
        root.addWidget(title)
        root.addWidget(QLabel("保持原图尺寸与格式，处理结果另存到输出目录。", objectName="pageSubtitle"))
        root.addSpacing(8)

        splitter = QSplitter()
        splitter.addWidget(self._files_panel())
        splitter.addWidget(self._settings_panel())
        splitter.setSizes([520, 440])
        root.addWidget(splitter, 1)
        root.addWidget(self._status_panel())

    def _files_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        group = QGroupBox("待处理图片")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)
        buttons = QHBoxLayout()
        choose_files = QPushButton("添加图片", objectName="primary")
        choose_folder = QPushButton("添加文件夹")
        clear = QPushButton("清空", objectName="ghost")
        choose_files.clicked.connect(self.choose_files)
        choose_folder.clicked.connect(self.choose_folder)
        clear.clicked.connect(self.clear_files)
        buttons.addWidget(choose_files)
        buttons.addWidget(choose_folder)
        buttons.addStretch()
        buttons.addWidget(clear)
        group_layout.addLayout(buttons)
        self.file_list = ImageDropList()
        self.file_list.filesDropped.connect(self.add_files)
        self.file_list.currentRowChanged.connect(lambda _: self.schedule_preview())
        group_layout.addWidget(self.file_list)
        count_row = QHBoxLayout()
        self.count_label = QLabel("0 张待处理", objectName="countChip")
        count_row.addWidget(self.count_label)
        count_row.addStretch()
        group_layout.addLayout(count_row)
        layout.addWidget(group, 1)

        preview_group = QGroupBox("实时预览（当前选中图片）")
        preview_layout = QVBoxLayout(preview_group)
        self.preview = PreviewLabel()
        preview_layout.addWidget(self.preview)
        layout.addWidget(preview_group, 2)
        return panel

    def _settings_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        group = QGroupBox("水印设置")
        form = QFormLayout(group)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(11)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.text_input = QLineEdit("仅供内部使用")
        self.font_size = self._spin(8, 240, 36, " px")
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(0, 255)
        self.opacity.setValue(128)
        self.opacity_value = QLabel("50%")
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(self.opacity)
        opacity_row.addWidget(self.opacity_value)
        self.opacity.valueChanged.connect(lambda value: self.opacity_value.setText(f"{round(value / 255 * 100)}%"))

        self.color = "#ffffff"
        self.color_button = QPushButton(self.color)
        self.color_button.setStyleSheet("background:#ffffff;color:#111827;")
        self.color_button.clicked.connect(self.choose_color)
        self.position = QComboBox()
        self.position.addItems(["左上", "右上", "左下", "右下", "居中"])
        self.position.setCurrentText("右下")
        self.margin = self._spin(0, 1000, 24, " px")
        self.tiled = QCheckBox("平铺水印")
        self.angle = self._spin(-180, 180, 30, "°")
        self.spacing = self._spin(0, 1000, 80, " px")
        self.angle.setEnabled(False)
        self.spacing.setEnabled(False)
        self.tiled.toggled.connect(self._toggle_tiling)

        form.addRow("文字", self.text_input)
        form.addRow("字体大小", self.font_size)
        form.addRow("透明度", opacity_row)
        form.addRow("文字颜色", self.color_button)
        form.addRow("位置", self.position)
        form.addRow("边距", self.margin)
        form.addRow("模式", self.tiled)
        form.addRow("平铺角度", self.angle)
        form.addRow("平铺间距", self.spacing)
        layout.addWidget(group)

        output_group = QGroupBox("输出")
        output_layout = QGridLayout(output_group)
        self.output_edit = QLineEdit(str(self.output_dir))
        browse = QPushButton("选择目录")
        browse.clicked.connect(self.choose_output)
        output_layout.addWidget(self.output_edit, 0, 0)
        output_layout.addWidget(browse, 0, 1)
        self.start_button = QPushButton("开始批量处理", objectName="primary")
        self.start_button.clicked.connect(self.start_processing)
        output_layout.addWidget(self.start_button, 1, 0, 1, 2)
        layout.addWidget(output_group)
        layout.addStretch()
        return panel

    def _status_panel(self) -> QWidget:
        panel = QWidget(objectName="statusPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(14, 9, 10, 9)
        layout.setSpacing(12)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.status = QLabel("就绪", objectName="statusText")
        self.open_button = QPushButton("打开输出目录")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_output)
        layout.addWidget(self.progress, 1)
        layout.addWidget(self.status)
        layout.addWidget(self.open_button)
        return panel

    @staticmethod
    def _spin(minimum: int, maximum: int, value: int, suffix: str) -> QSpinBox:
        box = QSpinBox()
        box.setRange(minimum, maximum)
        box.setValue(value)
        box.setSuffix(suffix)
        return box

    def _connect_preview_controls(self) -> None:
        self.text_input.textChanged.connect(self.schedule_preview)
        self.font_size.valueChanged.connect(self.schedule_preview)
        self.opacity.valueChanged.connect(self.schedule_preview)
        self.position.currentTextChanged.connect(self.schedule_preview)
        self.margin.valueChanged.connect(self.schedule_preview)
        self.tiled.toggled.connect(self.schedule_preview)
        self.angle.valueChanged.connect(self.schedule_preview)
        self.spacing.valueChanged.connect(self.schedule_preview)

    def _toggle_tiling(self, checked: bool) -> None:
        self.position.setEnabled(not checked)
        self.margin.setEnabled(not checked)
        self.angle.setEnabled(checked)
        self.spacing.setEnabled(checked)

    def choose_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.color), self, "选择水印颜色")
        if color.isValid():
            self.color = color.name()
            self.color_button.setText(self.color)
            self.color_button.setStyleSheet(f"background:{self.color};color:{'#111827' if color.lightness() > 150 else 'white'};")
            self.schedule_preview()

    def choose_files(self) -> None:
        names, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "图片 (*.jpg *.jpeg *.png *.webp)")
        self.add_files([Path(name) for name in names])

    def choose_folder(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if name:
            self.add_files(images_in_folder(Path(name)))

    def choose_output(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_edit.text())
        if name:
            self.output_edit.setText(name)

    def add_files(self, paths: list[Path]) -> None:
        known = {str(path.resolve()).lower() for path in self.sources}
        for path in paths:
            key = str(path.resolve()).lower()
            if key not in known:
                self.sources.append(path.resolve())
                self.file_list.addItem(str(path.resolve()))
                known.add(key)
        self.count_label.setText(f"{len(self.sources)} 张待处理")
        if self.sources and self.file_list.currentRow() < 0:
            self.file_list.setCurrentRow(0)
        self.schedule_preview()

    def clear_files(self) -> None:
        self.sources.clear()
        self.file_list.clear()
        self.count_label.setText("0 张待处理")
        self.preview.clear()
        self.preview.setText("图片预览\n选择或拖入图片后实时显示效果")

    def options(self) -> WatermarkOptions:
        return WatermarkOptions(
            text=self.text_input.text(),
            font_size=self.font_size.value(),
            opacity=self.opacity.value(),
            color=self.color,
            position=self.position.currentText(),
            margin=self.margin.value(),
            tiled=self.tiled.isChecked(),
            angle=self.angle.value(),
            spacing=self.spacing.value(),
        )

    def schedule_preview(self, *_args) -> None:
        self.preview_timer.start()

    def update_preview(self) -> None:
        row = self.file_list.currentRow()
        if row < 0 or row >= len(self.sources):
            return
        try:
            with Image.open(self.sources[row]) as image:
                image.thumbnail((900, 700), Image.Resampling.LANCZOS)
                rendered = render_watermark(image, self.options())
                self.preview.show_pixmap(QPixmap.fromImage(ImageQt(rendered)))
        except Exception as exc:
            self.preview.setText(f"预览失败：{exc}")

    def start_processing(self) -> None:
        if not self.sources:
            QMessageBox.information(self, "提示", "请先添加图片。")
            return
        if not self.text_input.text().strip():
            QMessageBox.information(self, "提示", "请输入水印文字。")
            return
        output = Path(self.output_edit.text().strip() or "output").resolve()
        self.output_dir = output
        self.progress.setRange(0, len(self.sources))
        self.progress.setValue(0)
        self.start_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.status.setText(f"处理中：0/{len(self.sources)}")
        self.worker = WatermarkWorker(self.sources.copy(), output, self.options())
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_completed)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _on_progress(self, done: int, total: int, success: int, failed: int) -> None:
        self.progress.setValue(done)
        self.status.setText(f"{done}/{total}  成功 {success}  失败 {failed}")

    def _on_completed(self, success: int, failed: int, failures: list[str]) -> None:
        self.start_button.setEnabled(True)
        self.open_button.setEnabled(True)
        summary = f"处理完成\n成功：{success} 张\n失败：{failed} 张\n输出目录：{self.output_dir}"
        if failures:
            summary += "\n\n失败详情：\n" + "\n".join(failures[:10])
        QMessageBox.information(self, "处理结果", summary)

    def _worker_finished(self) -> None:
        self.worker = None

    def stop_worker(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()

    def open_output(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        open_folder(self.output_dir)
