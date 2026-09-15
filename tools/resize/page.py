import os
from pathlib import Path

from PIL import Image, ImageOps
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidgetItem, QPushButton, QSplitter, QVBoxLayout, QWidget,
)

from app.icons import icon
from components.controls import AppComboBox, AppSpinBox
from components.dialogs import TaskDialog
from components.image_drop_list import ImageDropList
from components.preview_label import PreviewLabel
from services.image_resize import ResizeOptions, calculate_output_size, resize_image
from tools.resize.worker import ResizeWorker
from utils.image_files import images_in_folder


class ResizePage(QWidget):
    PRESETS = (("自定义", None), ("800 × 800", (800, 800)), ("1000 × 1000", (1000, 1000)),
               ("1200 × 1200", (1200, 1200)), ("1500 × 1500", (1500, 1500)), ("1920 × 1080", (1920, 1080)))

    def __init__(self) -> None:
        super().__init__()
        self.sources: list[Path] = []
        self.worker: ResizeWorker | None = None
        self.task_dialog: TaskDialog | None = None
        self.output_dir = Path.cwd() / "output"
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "resize")
        self._loading = False
        self.preview_timer = QTimer(self, interval=120, singleShot=True)
        self.preview_timer.timeout.connect(self.update_preview)
        self._build_ui()
        self._restore_settings()
        self._connect_controls()
        self._update_mode()
        self._update_file_state()

    def _build_ui(self) -> None:
        self.setObjectName("page")
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 14, 28, 20)
        root.setSpacing(6)
        root.addWidget(QLabel("批量修改图片尺寸", objectName="pageTitle"))
        root.addWidget(QLabel("统一图片尺寸或按比例缩放，原图不会被覆盖。", objectName="pageSubtitle"))
        root.addSpacing(8)
        splitter = QSplitter(objectName="workspaceSplitter")
        splitter.setChildrenCollapsible(False)
        left, right = self._files_panel(), self._settings_panel()
        left.setMinimumWidth(400)
        right.setMinimumWidth(340)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([640, 420])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

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

    @staticmethod
    def _spin(value: int) -> AppSpinBox:
        box = AppSpinBox()
        box.setRange(1, 20000)
        box.setValue(value)
        box.setSuffix(" px")
        return box

    def _files_panel(self) -> QWidget:
        card, layout = self._card("图片预览")
        self.preview = PreviewLabel()
        self.preview.filesDropped.connect(self.add_files)
        self.preview.chooseFilesRequested.connect(self.choose_files)
        self.preview.chooseFolderRequested.connect(self.choose_folder)
        layout.addWidget(self.preview, 1)
        self.image_info = QLabel("", objectName="helperText")
        self.image_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_info)
        self.file_actions = QWidget()
        actions = QHBoxLayout(self.file_actions)
        actions.setContentsMargins(0, 0, 0, 0)
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
        self.count_label = QLabel("共 0 张", objectName="countLabel")
        actions.addWidget(self.count_label)
        actions.addWidget(clear)
        layout.addWidget(self.file_actions)
        self.file_list = ImageDropList()
        self.file_list.setMinimumHeight(80)
        self.file_list.setMaximumHeight(136)
        self.file_list.filesDropped.connect(self.add_files)
        self.file_list.currentRowChanged.connect(self.schedule_preview)
        layout.addWidget(self.file_list)
        return card

    def _settings_panel(self) -> QWidget:
        card, layout = self._card("调整尺寸")
        self.settings_card = card
        self.mode = AppComboBox()
        for text, data in (("固定尺寸", "fixed"), ("指定宽度", "width"), ("指定高度", "height"), ("限制最大尺寸", "max")):
            self.mode.addItem(text, data)
        layout.addWidget(self._field("调整方式", self.mode))
        self.preset = AppComboBox()
        for text, data in self.PRESETS:
            self.preset.addItem(text, data)
        layout.addWidget(self._field("预设", self.preset))
        self.width_input, self.height_input = self._spin(800), self._spin(800)
        dimensions = QGridLayout()
        dimensions.setColumnStretch(0, 1)
        dimensions.setColumnStretch(1, 1)
        self.width_field = self._field("宽度", self.width_input)
        self.height_field = self._field("高度", self.height_input)
        dimensions.addWidget(self.width_field, 0, 0)
        dimensions.addWidget(self.height_field, 0, 1)
        layout.addLayout(dimensions)
        self.fit_mode = AppComboBox()
        for text, data in (("等比留白", "contain"), ("等比裁剪", "cover"), ("拉伸", "stretch")):
            self.fit_mode.addItem(text, data)
        self.fit_field = self._field("适配方式", self.fit_mode)
        layout.addWidget(self.fit_field)
        self.stretch_notice = QLabel("图片比例可能发生变化。", objectName="warningText")
        layout.addWidget(self.stretch_notice)
        self.prevent_upscale = QCheckBox("不放大小图")
        self.prevent_upscale.setChecked(True)
        layout.addWidget(self.prevent_upscale)
        self.color = "#ffffff"
        self.color_button = QPushButton()
        self.color_button.clicked.connect(self.choose_color)
        self.color_field = self._field("背景颜色", self.color_button)
        layout.addWidget(self.color_field)
        self._update_color_button()
        layout.addStretch()
        self.output_edit = QLineEdit(str(self.output_dir))
        self.output_edit.hide()
        self.output_button = QPushButton(objectName="outputButton")
        self.output_button.setIcon(icon("folder-open"))
        self.output_button.clicked.connect(self.choose_output)
        layout.addWidget(self.output_button)
        self.output_error = QLabel("", objectName="fieldError")
        layout.addWidget(self.output_error)
        self.start_hint = QLabel("请先添加图片", objectName="helperText")
        layout.addWidget(self.start_hint)
        self.start_button = QPushButton("开始批量处理", objectName="startButton")
        self.start_button.clicked.connect(self.start_processing)
        layout.addWidget(self.start_button)
        return card

    def _connect_controls(self) -> None:
        self.mode.currentIndexChanged.connect(self._update_mode)
        self.preset.currentIndexChanged.connect(self._apply_preset)
        self.fit_mode.currentIndexChanged.connect(self._update_mode)
        self.width_input.valueChanged.connect(self._dimensions_changed)
        self.height_input.valueChanged.connect(self._dimensions_changed)
        self.prevent_upscale.toggled.connect(self.schedule_preview)
        self.color_button.clicked.connect(self.schedule_preview)
        self.output_edit.textChanged.connect(self._update_start_button)
        for signal in (self.mode.currentIndexChanged, self.preset.currentIndexChanged, self.fit_mode.currentIndexChanged,
                       self.width_input.valueChanged, self.height_input.valueChanged, self.prevent_upscale.toggled, self.output_edit.textChanged):
            signal.connect(self._save_settings)

    def _update_mode(self, *_args) -> None:
        mode = self.mode.currentData()
        fixed = mode == "fixed"
        self.width_field.setVisible(mode != "height")
        self.height_field.setVisible(mode != "width")
        self.preset.setEnabled(fixed)
        self.fit_field.setVisible(fixed)
        self.stretch_notice.setVisible(fixed and self.fit_mode.currentData() == "stretch")
        self.color_field.setVisible(fixed and self.fit_mode.currentData() == "contain")
        self.schedule_preview()

    def _apply_preset(self, *_args) -> None:
        value = self.preset.currentData()
        if value:
            self._loading = True
            self.width_input.setValue(value[0])
            self.height_input.setValue(value[1])
            self._loading = False
        self.schedule_preview()

    def _dimensions_changed(self, *_args) -> None:
        if not self._loading and self.preset.currentData() not in (None, (self.width_input.value(), self.height_input.value())):
            self.preset.setCurrentIndex(0)
        self.schedule_preview()

    def options(self) -> ResizeOptions:
        return ResizeOptions(self.mode.currentData(), self.width_input.value(), self.height_input.value(), self.fit_mode.currentData(),
                             self.prevent_upscale.isChecked(), self.color)

    def choose_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.color), self, "选择背景颜色")
        if color.isValid():
            self.color = color.name()
            self._update_color_button()
            self._save_settings()

    def _update_color_button(self) -> None:
        swatch = QPixmap(16, 16)
        swatch.fill(QColor(self.color))
        self.color_button.setIcon(QIcon(swatch))
        self.color_button.setText(self.color.upper())

    def choose_files(self) -> None:
        names, _ = QFileDialog.getOpenFileNames(self, "选择图片", self._source_dir(), "图片 (*.jpg *.jpeg *.png *.webp)")
        if names:
            self.add_files([Path(name) for name in names])

    def choose_folder(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择图片文件夹", self._source_dir())
        if name:
            self.add_files(images_in_folder(Path(name)))

    def _source_dir(self) -> str:
        path = Path(self.settings.value("source_dir", "", type=str))
        return str(path) if path.is_dir() else str(Path.home())

    def choose_output(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_edit.text())
        if name:
            self.output_edit.setText(name)

    def add_files(self, paths: list[Path]) -> None:
        known = {str(path).lower() for path in self.sources}
        for path in paths:
            resolved = path.resolve()
            if not resolved.is_file() or resolved.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"} or str(resolved).lower() in known:
                continue
            self.sources.append(resolved)
            self.file_list.addItem(QListWidgetItem(resolved.name))
            known.add(str(resolved).lower())
        if paths:
            parent = paths[0] if paths[0].is_dir() else paths[0].parent
            self.settings.setValue("source_dir", str(parent.resolve()))
        if self.sources and self.file_list.currentRow() < 0:
            self.file_list.setCurrentRow(0)
        self._update_file_state()
        self.schedule_preview()

    def clear_files(self) -> None:
        self.sources.clear()
        self.file_list.clear()
        self.preview.clear()
        self.image_info.clear()
        self._update_file_state()

    def _update_file_state(self) -> None:
        count = len(self.sources)
        self.count_label.setText(f"共 {count} 张")
        self.file_actions.setVisible(bool(count))
        self.file_list.setVisible(bool(count))
        self.start_button.setText(f"开始处理 {count} 张图片" if count else "开始批量处理")
        self._update_start_button()

    def _valid_output(self) -> bool:
        text = self.output_edit.text().strip()
        valid, message = bool(text), "请选择输出目录"
        if valid:
            try:
                path = Path(text)
                if path.exists() and not path.is_dir():
                    valid, message = False, "输出路径不能是文件"
                else:
                    parent = path
                    while not parent.exists() and parent != parent.parent:
                        parent = parent.parent
                    valid, message = parent.is_dir() and os.access(parent, os.W_OK), "请选择有效且可写的输出目录"
            except OSError:
                valid, message = False, "输出目录格式无效"
        self.output_button.setText(f"输出到：{Path(text).name}" if text else "选择输出目录")
        self.output_button.setToolTip(text)
        self.output_error.setText("" if valid else message)
        self.output_error.setVisible(not valid)
        return valid

    def _update_start_button(self, *_args) -> None:
        valid = self._valid_output()
        self.start_button.setEnabled(bool(self.sources and valid and self.worker is None))
        self.start_hint.setText("正在处理，请稍候" if self.worker else "请先添加图片" if not self.sources else "请修正输出目录" if not valid else "参数就绪，可以开始处理")

    def schedule_preview(self, *_args) -> None:
        self.preview_timer.start()

    def update_preview(self) -> None:
        row = self.file_list.currentRow()
        if not 0 <= row < len(self.sources):
            return
        try:
            with Image.open(self.sources[row]) as original:
                oriented = ImageOps.exif_transpose(original)
                source_size = oriented.size
                expected = calculate_output_size(source_size, self.options())
                rendered = resize_image(oriented, self.options())
                rendered.thumbnail((900, 700), Image.Resampling.LANCZOS)
                self.preview.show_pixmap(QPixmap.fromImage(ImageQt(rendered)))
                self.image_info.setText(f"原始尺寸 {source_size[0]} × {source_size[1]}  →  预计输出 {expected[0]} × {expected[1]} px")
        except Exception as exc:
            self.preview.setText(f"预览失败：{exc}")

    def _save_settings(self, *_args) -> None:
        if self._loading:
            return
        values = {"mode": self.mode.currentData(), "width": self.width_input.value(), "height": self.height_input.value(),
                  "fit_mode": self.fit_mode.currentData(), "prevent_upscale": self.prevent_upscale.isChecked(),
                  "background_color": self.color, "preset": self.preset.currentIndex(), "output_dir": self.output_edit.text().strip()}
        for key, value in values.items():
            self.settings.setValue(key, value)
        self.settings.sync()

    def _restore_settings(self) -> None:
        self._loading = True
        try:
            for combo, key, default in ((self.mode, "mode", "fixed"), (self.fit_mode, "fit_mode", "contain")):
                index = combo.findData(self.settings.value(key, default, type=str))
                combo.setCurrentIndex(index if index >= 0 else 0)
            for box, key in ((self.width_input, "width"), (self.height_input, "height")):
                try:
                    box.setValue(int(self.settings.value(key, 800)))
                except (TypeError, ValueError):
                    box.setValue(800)
            self.prevent_upscale.setChecked(self.settings.value("prevent_upscale", True, type=bool))
            color = self.settings.value("background_color", "#ffffff", type=str)
            self.color = color if QColor(color).isValid() else "#ffffff"
            self._update_color_button()
            self.preset.setCurrentIndex(min(max(int(self.settings.value("preset", 1)), 0), self.preset.count() - 1))
            output = Path(self.settings.value("output_dir", str(self.output_dir), type=str))
            self.output_edit.setText(str(output) if output.is_dir() else str(self.output_dir))
        finally:
            self._loading = False

    def _set_processing(self, processing: bool) -> None:
        self.file_list.setEnabled(not processing)
        self.file_actions.setEnabled(not processing)
        self.settings_card.setEnabled(not processing)

    def start_processing(self) -> None:
        if self.worker or not self.start_button.isEnabled():
            return
        output = Path(self.output_edit.text()).resolve()
        self.output_dir = output
        self.task_dialog = TaskDialog(len(self.sources), output, self, clear_task_inputs=self.clear_files)
        self.worker = ResizeWorker(self.sources.copy(), output, self.options())
        self.worker.progress.connect(lambda done, total, success, failed: self.task_dialog and self.task_dialog.update_progress(done, total, success, failed))
        self.worker.completed.connect(lambda success, failed, failures: self.task_dialog and self.task_dialog.show_result(success, failed, failures))
        self.worker.finished.connect(self._worker_finished)
        self._set_processing(True)
        self._update_start_button()
        self.worker.start()
        self.task_dialog.open()

    def _worker_finished(self) -> None:
        if self.task_dialog and self.task_dialog.processing:
            self.task_dialog.show_result(self.task_dialog.success, self.task_dialog.total - self.task_dialog.success, ["任务异常结束"], completed=False)
        self.worker = None
        self._set_processing(False)
        self._update_start_button()

    def stop_worker(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()
