from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.icons import icon
from components.image_drop_list import ImageDropList
from components.preview_label import PreviewLabel
from services.image_processing import WatermarkOptions, render_watermark
from tools.watermark.worker import WatermarkWorker
from utils.image_files import images_in_folder
from utils.system import open_folder


class ImageListRow(QWidget):
    clicked = Signal()
    removeRequested = Signal()

    def __init__(self, path: Path) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 4, 0)
        layout.setSpacing(8)
        name = QLabel(path.name)
        name.setToolTip(str(path))
        size = QLabel(self._format_size(path), objectName="fieldValue")
        remove = QPushButton("×", objectName="rowRemove")
        remove.setToolTip(f"移除 {path.name}")
        remove.clicked.connect(self.removeRequested)
        layout.addWidget(name, 1)
        layout.addWidget(size)
        layout.addWidget(remove)

    @staticmethod
    def _format_size(path: Path) -> str:
        size = path.stat().st_size
        return f"{size / 1024:.0f} KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f} MB"

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)


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
        self._update_file_state()

    def _build_ui(self) -> None:
        self.setObjectName("page")
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 12, 32, 20)
        root.setSpacing(8)
        root.addWidget(QLabel("图片工具 / 批量打水印", objectName="pageEyebrow"))
        root.addWidget(QLabel("批量打水印", objectName="pageTitle"))
        root.addWidget(QLabel("批量为图片添加统一文字水印，原图不会被覆盖。", objectName="pageSubtitle"))
        root.addSpacing(8)

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._files_panel())
        splitter.addWidget(self._settings_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([640, 420])
        root.addWidget(splitter, 1)
        root.addWidget(self._status_panel())

    @staticmethod
    def _card(title: str) -> tuple[QWidget, QVBoxLayout]:
        card = QWidget(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(QLabel(title, objectName="cardTitle"))
        return card, layout

    def _files_panel(self) -> QWidget:
        card, layout = self._card("图片预览")
        self.preview = PreviewLabel()
        self.preview.filesDropped.connect(self.add_files)
        layout.addWidget(self.preview, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        choose_files = QPushButton("添加图片", objectName="primary")
        choose_files.setIcon(icon("plus", "#FFFFFF"))
        choose_folder = QPushButton("添加文件夹")
        choose_folder.setIcon(icon("folder"))
        clear = QPushButton("清空全部", objectName="ghost")
        choose_files.clicked.connect(self.choose_files)
        choose_folder.clicked.connect(self.choose_folder)
        clear.clicked.connect(self.clear_files)
        actions.addWidget(choose_files)
        actions.addWidget(choose_folder)
        actions.addStretch()
        self.count_label = QLabel("已添加 0 张", objectName="countLabel")
        actions.addWidget(self.count_label)
        actions.addWidget(clear)
        layout.addLayout(actions)

        self.file_list = ImageDropList()
        self.file_list.setMinimumHeight(72)
        self.file_list.setMaximumHeight(128)
        self.file_list.filesDropped.connect(self.add_files)
        self.file_list.currentRowChanged.connect(lambda _: self.schedule_preview())
        layout.addWidget(self.file_list)
        return card

    def _settings_panel(self) -> QWidget:
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(16)
        scroll = QScrollArea(objectName="settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(0)

        settings, form = self._card("水印设置")
        self.text_input = QLineEdit("仅供内部使用")
        self.font_size = self._spin(8, 240, 36, " px")
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(0, 255)
        self.opacity.setValue(128)
        self.opacity_value = QLabel("50%", objectName="fieldValue")
        opacity_title = QHBoxLayout()
        opacity_title.addWidget(QLabel("透明度", objectName="fieldLabel"))
        opacity_title.addStretch()
        opacity_title.addWidget(self.opacity_value)
        self.opacity.valueChanged.connect(lambda value: self.opacity_value.setText(f"{round(value / 255 * 100)}%"))

        self.color = "#ffffff"
        self.color_button = QPushButton()
        self._update_color_button()
        self.color_button.clicked.connect(self.choose_color)
        self.position = QComboBox()
        self.position.addItems(["左上", "右上", "左下", "右下", "居中"])
        self.position.setCurrentText("右下")
        self.margin = self._spin(0, 1000, 24, " px")
        self.tiled = QCheckBox("启用平铺")
        self.angle = self._spin(-180, 180, 30, "°")
        self.spacing = self._spin(0, 1000, 80, " px")
        self.angle.setEnabled(False)
        self.spacing.setEnabled(False)
        self.tiled.toggled.connect(self._toggle_tiling)

        self._field(form, "水印文字", self.text_input)
        self._field(form, "字体大小", self.font_size)
        form.addLayout(opacity_title)
        form.addWidget(self.opacity)
        self._field(form, "文字颜色", self.color_button)
        self._field(form, "水印位置", self.position)
        self._field(form, "边距", self.margin)
        self._field(form, "平铺水印", self.tiled)
        self._field(form, "平铺角度", self.angle)
        self._field(form, "平铺间距", self.spacing)
        layout.addWidget(settings)
        layout.addStretch()
        scroll.setWidget(panel)
        container_layout.addWidget(scroll, 1)

        output, output_layout = self._card("输出设置")
        output_layout.addWidget(QLabel("输出目录", objectName="fieldLabel"))
        output_row = QHBoxLayout()
        self.output_edit = QLineEdit(str(self.output_dir))
        browse = QPushButton("选择")
        browse.setIcon(icon("folder-open"))
        browse.clicked.connect(self.choose_output)
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(browse)
        output_layout.addLayout(output_row)
        output_layout.addWidget(QLabel("结果将保存到新的文件，不会覆盖原图。", objectName="helperText"))
        self.start_button = QPushButton("开始批量处理", objectName="startButton")
        self.start_button.clicked.connect(self.start_processing)
        output_layout.addWidget(self.start_button)
        container_layout.addWidget(output)
        return container

    @staticmethod
    def _field(layout: QVBoxLayout, label: str, widget: QWidget) -> None:
        layout.addWidget(QLabel(label, objectName="fieldLabel"))
        layout.addWidget(widget)

    def _status_panel(self) -> QWidget:
        panel = QWidget(objectName="statusPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(8)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        row = QHBoxLayout()
        self.progress_count = QLabel("0 / 0", objectName="statusText")
        self.status = QLabel("就绪", objectName="statusText")
        self.open_button = QPushButton("打开输出目录")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_output)
        row.addWidget(self.progress_count)
        row.addStretch()
        row.addWidget(self.status)
        row.addWidget(self.open_button)
        layout.addLayout(row)
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
        self.text_input.textChanged.connect(self._update_start_button)
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
            self._update_color_button()
            self.schedule_preview()

    def _update_color_button(self) -> None:
        swatch = QPixmap(16, 16)
        swatch.fill(QColor(self.color))
        self.color_button.setIcon(QIcon(swatch))
        self.color_button.setText(self.color.upper())

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
            resolved = path.resolve()
            key = str(resolved).lower()
            if key in known:
                continue
            self.sources.append(resolved)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 40))
            self.file_list.addItem(item)
            row = ImageListRow(resolved)
            row.clicked.connect(lambda item=item: self.file_list.setCurrentItem(item))
            row.removeRequested.connect(lambda item=item: self._remove_item(item))
            self.file_list.setItemWidget(item, row)
            known.add(key)
        if self.sources and self.file_list.currentRow() < 0:
            self.file_list.setCurrentRow(0)
        self._update_file_state()
        self.schedule_preview()

    def _remove_item(self, item: QListWidgetItem) -> None:
        row = self.file_list.row(item)
        if row < 0:
            return
        self.sources.pop(row)
        self.file_list.takeItem(row)
        if self.sources and self.file_list.currentRow() < 0:
            self.file_list.setCurrentRow(min(row, len(self.sources) - 1))
        elif not self.sources:
            self.preview.clear()
        self._update_file_state()
        self.schedule_preview()

    def clear_files(self) -> None:
        self.sources.clear()
        self.file_list.clear()
        self.preview.clear()
        self._update_file_state()

    def _update_file_state(self) -> None:
        count = len(self.sources)
        self.count_label.setText(f"已添加 {count} 张")
        self.start_button.setText(f"开始处理 {count} 张图片" if count else "开始批量处理")
        self._update_start_button()

    def _update_start_button(self) -> None:
        self.start_button.setEnabled(bool(self.sources and self.text_input.text().strip() and self.worker is None))

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
        if not self.start_button.isEnabled():
            return
        output = Path(self.output_edit.text().strip() or "output").resolve()
        self.output_dir = output
        self.progress.setRange(0, len(self.sources))
        self.progress.setValue(0)
        self.open_button.setEnabled(False)
        self._set_status("处理中…")
        self.progress_count.setText(f"0 / {len(self.sources)}")
        self.worker = WatermarkWorker(self.sources.copy(), output, self.options())
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_completed)
        self.worker.finished.connect(self._worker_finished)
        self._update_start_button()
        self.worker.start()

    def _on_progress(self, done: int, total: int, success: int, failed: int) -> None:
        self.progress.setValue(done)
        self.progress_count.setText(f"{done} / {total}")
        self._set_status(f"处理中… 成功 {success} · 失败 {failed}")

    def _on_completed(self, success: int, failed: int, failures: list[str]) -> None:
        self.open_button.setEnabled(True)
        if failed == 0:
            self._set_status(f"✓ 处理完成 · 成功 {success} 张", "success")
        elif success:
            self._set_status(f"完成 · 成功 {success} · 失败 {failed}", "warning")
        else:
            self._set_status(f"处理失败 · 失败 {failed} 张", "danger")
        summary = f"处理完成\n成功：{success} 张\n失败：{failed} 张\n输出目录：{self.output_dir}"
        if failures:
            summary += "\n\n失败详情：\n" + "\n".join(failures[:10])
        QMessageBox.information(self, "处理结果", summary)

    def _set_status(self, text: str, status: str = "") -> None:
        self.status.setText(text)
        self.status.setProperty("status", status)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def _worker_finished(self) -> None:
        self.worker = None
        self._update_start_button()

    def stop_worker(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()

    def open_output(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        open_folder(self.output_dir)
