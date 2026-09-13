import os
from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSettings, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QPushButton,
    QProgressBar,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.icons import icon
from components.controls import AppComboBox, AppSpinBox, NoWheelSlider, RecentTextComboBox
from components.dialogs import ResultDialog
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
    DEFAULT_TEXT = "仅供内部使用"
    DEFAULT_FONT_SIZE = 24
    DEFAULT_OPACITY = 128
    DEFAULT_COLOR = "#ffffff"
    DEFAULT_POSITION = "右下"
    DEFAULT_MARGIN = 24
    DEFAULT_TILED = False
    DEFAULT_ANGLE = 30
    DEFAULT_SPACING = 80

    def __init__(self) -> None:
        super().__init__()
        self.sources: list[Path] = []
        self.output_dir = Path.cwd() / "output"
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "watermark")
        self._loading_settings = False
        self.worker: WatermarkWorker | None = None
        self.preview_timer = QTimer(self)
        self.preview_timer.setInterval(120)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        self._build_ui()
        self._restore_settings()
        self._connect_preview_controls()
        self._connect_settings_persistence()
        self._update_file_state()

    def _build_ui(self) -> None:
        self.setObjectName("page")
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 14, 28, 20)
        root.setSpacing(6)
        root.addWidget(QLabel("批量打水印", objectName="pageTitle"))
        root.addWidget(QLabel("批量为图片添加统一文字水印，原图不会被覆盖。", objectName="pageSubtitle"))
        root.addSpacing(8)

        splitter = QSplitter()
        splitter.setObjectName("workspaceSplitter")
        splitter.setChildrenCollapsible(False)
        files_panel = self._files_panel()
        settings_panel = self._settings_panel()
        files_panel.setMinimumWidth(400)
        settings_panel.setMinimumWidth(340)
        splitter.addWidget(files_panel)
        splitter.addWidget(settings_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([640, 420])
        root.addWidget(splitter, 1)
        self.status_panel = self._status_panel()
        self.status_panel.hide()
        root.addWidget(self.status_panel)

    @staticmethod
    def _card(title: str, action: QWidget | None = None) -> tuple[QWidget, QVBoxLayout]:
        card = QWidget(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(QLabel(title, objectName="cardTitle"))
        header.addStretch()
        if action is not None:
            header.addWidget(action)
        layout.addLayout(header)
        return card, layout

    def _files_panel(self) -> QWidget:
        card, layout = self._card("图片预览")
        self.preview = PreviewLabel()
        self.preview.filesDropped.connect(self.add_files)
        self.preview.chooseFilesRequested.connect(self.choose_files)
        self.preview.chooseFolderRequested.connect(self.choose_folder)
        layout.addWidget(self.preview, 1)

        self.file_actions = QWidget()
        actions = QHBoxLayout(self.file_actions)
        actions.setContentsMargins(0, 0, 0, 0)
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
        self.count_label = QLabel("共 0 张", objectName="countLabel")
        actions.addWidget(self.count_label)
        actions.addWidget(clear)
        layout.addWidget(self.file_actions)

        self.file_list = ImageDropList()
        self.file_list.setMinimumHeight(80)
        self.file_list.setMaximumHeight(136)
        self.file_list.filesDropped.connect(self.add_files)
        self.file_list.currentRowChanged.connect(lambda _: self.schedule_preview())
        layout.addWidget(self.file_list)
        return card

    def _settings_panel(self) -> QWidget:
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        self.reset_button = QPushButton("恢复默认", objectName="ghost")
        self.reset_button.clicked.connect(self.restore_defaults)
        self.settings_card, settings_layout = self._card("水印设置", self.reset_button)
        settings_layout.setSpacing(14)

        self.text_input = RecentTextComboBox()
        self.text_input.setText(self.DEFAULT_TEXT)
        self.font_size = self._spin(8, 240, self.DEFAULT_FONT_SIZE, " px")
        self.opacity = NoWheelSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(0, 255)
        self.opacity.setValue(self.DEFAULT_OPACITY)
        self.opacity_value = QLabel("50%", objectName="fieldValue")
        opacity_title = QHBoxLayout()
        opacity_title.addWidget(QLabel("透明度", objectName="fieldLabel"))
        opacity_title.addStretch()
        opacity_title.addWidget(self.opacity_value)
        self.opacity.valueChanged.connect(lambda value: self.opacity_value.setText(f"{round(value / 255 * 100)}%"))

        self.color = self.DEFAULT_COLOR
        self.color_button = QPushButton()
        self._update_color_button()
        self.color_button.clicked.connect(self.choose_color)
        self.position = AppComboBox()
        self.position.addItems(["左上", "右上", "左下", "右下", "居中"])
        self.position.setCurrentText(self.DEFAULT_POSITION)
        self.margin = self._spin(0, 1000, self.DEFAULT_MARGIN, " px")
        self.tiled = QCheckBox("启用平铺")
        self.angle = self._spin(-180, 180, self.DEFAULT_ANGLE, "°")
        self.spacing = self._spin(0, 1000, self.DEFAULT_SPACING, " px")
        self.angle.setEnabled(False)
        self.spacing.setEnabled(False)
        self.tiled.toggled.connect(self._toggle_tiling)

        self._field(settings_layout, "水印文字", self.text_input)

        essentials = QGridLayout()
        essentials.setContentsMargins(0, 0, 0, 0)
        essentials.setHorizontalSpacing(12)
        essentials.setVerticalSpacing(14)
        essentials.setColumnStretch(0, 1)
        essentials.setColumnStretch(1, 1)
        essentials.addWidget(self._field_widget("字体大小", self.font_size), 0, 0)
        essentials.addWidget(self._field_widget("文字颜色", self.color_button), 0, 1)
        settings_layout.addLayout(essentials)

        settings_layout.addLayout(opacity_title)
        settings_layout.addWidget(self.opacity)

        position_grid = QGridLayout()
        position_grid.setContentsMargins(0, 0, 0, 0)
        position_grid.setHorizontalSpacing(12)
        position_grid.setColumnStretch(0, 1)
        position_grid.setColumnStretch(1, 1)
        self.position_field = self._field_widget("水印位置", self.position)
        self.margin_field = self._field_widget("边距", self.margin)
        self.angle_field = self._field_widget("平铺角度", self.angle)
        self.spacing_field = self._field_widget("平铺间距", self.spacing)
        position_grid.addWidget(self.position_field, 0, 0)
        position_grid.addWidget(self.angle_field, 0, 0)
        position_grid.addWidget(self.margin_field, 0, 1)
        position_grid.addWidget(self.spacing_field, 0, 1)
        settings_layout.addLayout(position_grid)
        settings_layout.addWidget(self.tiled)
        settings_layout.addStretch()

        self.output_edit = QLineEdit(str(self.output_dir))
        self.output_edit.hide()
        self.output_edit.setToolTip(str(self.output_dir))
        self.output_button = QPushButton(objectName="outputButton")
        self.output_button.setIcon(icon("folder-open"))
        self.output_button.clicked.connect(self.choose_output)
        settings_layout.addWidget(self.output_button)
        self.output_error = QLabel("", objectName="fieldError")
        self.output_error.hide()
        settings_layout.addWidget(self.output_error)
        self.output_notice = QLabel("", objectName="warningText")
        self.output_notice.setWordWrap(True)
        self.output_notice.hide()
        settings_layout.addWidget(self.output_notice)
        self.start_hint = QLabel("请先添加图片", objectName="helperText")
        settings_layout.addWidget(self.start_hint)
        self.start_button = QPushButton("开始批量处理", objectName="startButton")
        self.start_button.clicked.connect(self.start_processing)
        settings_layout.addWidget(self.start_button)
        container_layout.addWidget(self.settings_card, 1)
        self.output_edit.textChanged.connect(self._update_start_button)
        self._toggle_tiling(False)
        return container

    @staticmethod
    def _field(layout: QVBoxLayout, label: str, widget: QWidget) -> QWidget:
        field = WatermarkPage._field_widget(label, widget)
        layout.addWidget(field)
        return field

    @staticmethod
    def _field_widget(label: str, widget: QWidget) -> QWidget:
        field = QWidget(objectName="field")
        field_layout = QVBoxLayout(field)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(6)
        field_layout.addWidget(QLabel(label, objectName="fieldLabel"))
        field_layout.addWidget(widget)
        return field

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
    def _spin(minimum: int, maximum: int, value: int, suffix: str) -> AppSpinBox:
        box = AppSpinBox()
        box.setRange(minimum, maximum)
        box.setValue(value)
        box.setSuffix(suffix)
        return box

    def _connect_preview_controls(self) -> None:
        self.text_input.currentTextChanged.connect(self.schedule_preview)
        self.text_input.currentTextChanged.connect(self._update_start_button)
        self.font_size.valueChanged.connect(self.schedule_preview)
        self.opacity.valueChanged.connect(self.schedule_preview)
        self.position.currentTextChanged.connect(self.schedule_preview)
        self.margin.valueChanged.connect(self.schedule_preview)
        self.tiled.toggled.connect(self.schedule_preview)
        self.angle.valueChanged.connect(self.schedule_preview)
        self.spacing.valueChanged.connect(self.schedule_preview)

    def _connect_settings_persistence(self) -> None:
        for signal in (
            self.text_input.currentTextChanged,
            self.font_size.valueChanged,
            self.opacity.valueChanged,
            self.position.currentTextChanged,
            self.margin.valueChanged,
            self.tiled.toggled,
            self.angle.valueChanged,
            self.spacing.valueChanged,
            self.output_edit.textChanged,
        ):
            signal.connect(self._save_settings)

    def _saved_value(self, key: str, default, value_type):
        try:
            return self.settings.value(key, default, type=value_type)
        except (TypeError, ValueError):
            return default

    def _saved_int(self, key: str, default: int, minimum: int, maximum: int) -> int:
        raw = self.settings.value(key, default)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return default
        return value if minimum <= value <= maximum else default

    def _restore_settings(self) -> None:
        self._loading_settings = True
        try:
            history = self.settings.value("recent_texts", [])
            history = [history] if isinstance(history, str) else history if isinstance(history, list) else []
            history = list(dict.fromkeys(text.strip() for text in history if isinstance(text, str) and text.strip()))[:3]
            self.text_input.set_history(history)
            self.text_input.setText(self._saved_value("text", self.DEFAULT_TEXT, str))
            self.font_size.setValue(self._saved_int("font_size", self.DEFAULT_FONT_SIZE, 8, 240))
            self.opacity.setValue(self._saved_int("opacity", self.DEFAULT_OPACITY, 0, 255))
            color = self._saved_value("color", self.DEFAULT_COLOR, str)
            self.color = color if QColor(color).isValid() else self.DEFAULT_COLOR
            self._update_color_button()
            position = self._saved_value("position", self.DEFAULT_POSITION, str)
            self.position.setCurrentText(position if self.position.findText(position) >= 0 else self.DEFAULT_POSITION)
            self.margin.setValue(self._saved_int("margin", self.DEFAULT_MARGIN, 0, 1000))
            self.tiled.setChecked(self._saved_value("tiled", self.DEFAULT_TILED, bool))
            self.angle.setValue(self._saved_int("angle", self.DEFAULT_ANGLE, -180, 180))
            self.spacing.setValue(self._saved_int("spacing", self.DEFAULT_SPACING, 0, 1000))

            previous_output = self.settings.value("output_dir")
            if previous_output is not None and self._existing_output_dir(str(previous_output)):
                self.output_edit.setText(str(previous_output))
                self.output_dir = Path(str(previous_output))
            elif previous_output is not None:
                self.output_edit.setText(str(self.output_dir))
                self.output_notice.setText("上次使用的输出目录不可用，请重新选择。")
                self.output_notice.show()
                self.settings.setValue("output_dir", str(self.output_dir))
                self.settings.sync()
        finally:
            self._loading_settings = False

    @staticmethod
    def _existing_output_dir(value: str) -> bool:
        try:
            path = Path(value)
            return path.is_dir() and os.access(path, os.W_OK)
        except OSError:
            return False

    def _save_settings(self, *_args) -> None:
        if self._loading_settings:
            return
        values = {
            "version": 1,
            "text": self.text_input.text(),
            "font_size": self.font_size.value(),
            "opacity": self.opacity.value(),
            "color": self.color,
            "position": self.position.currentText(),
            "margin": self.margin.value(),
            "tiled": self.tiled.isChecked(),
            "angle": self.angle.value(),
            "spacing": self.spacing.value(),
            "output_dir": self.output_edit.text().strip(),
        }
        for key, value in values.items():
            self.settings.setValue(key, value)
        self.settings.sync()

    def restore_defaults(self) -> None:
        self._loading_settings = True
        try:
            self.text_input.setText(self.DEFAULT_TEXT)
            self.font_size.setValue(self.DEFAULT_FONT_SIZE)
            self.opacity.setValue(self.DEFAULT_OPACITY)
            self.color = self.DEFAULT_COLOR
            self._update_color_button()
            self.position.setCurrentText(self.DEFAULT_POSITION)
            self.margin.setValue(self.DEFAULT_MARGIN)
            self.tiled.setChecked(self.DEFAULT_TILED)
            self.angle.setValue(self.DEFAULT_ANGLE)
            self.spacing.setValue(self.DEFAULT_SPACING)
        finally:
            self._loading_settings = False
        self._toggle_tiling(False)
        self._save_settings()
        self.schedule_preview()

    def _remember_current_text(self) -> None:
        text = self.text_input.text().strip()
        if not text:
            return
        history = [text, *(item for item in self.text_input.history() if item != text)][:3]
        self.text_input.set_history(history)
        self.settings.setValue("recent_texts", history)
        self.settings.sync()

    def _toggle_tiling(self, checked: bool) -> None:
        self.position_field.setVisible(not checked)
        self.margin_field.setVisible(not checked)
        self.angle_field.setVisible(checked)
        self.spacing_field.setVisible(checked)
        self.angle.setEnabled(checked)
        self.spacing.setEnabled(checked)

    def choose_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.color), self, "选择水印颜色")
        if color.isValid():
            self.color = color.name()
            self._update_color_button()
            self._save_settings()
            self.schedule_preview()

    def _update_color_button(self) -> None:
        swatch = QPixmap(16, 16)
        swatch.fill(QColor(self.color))
        self.color_button.setIcon(QIcon(swatch))
        self.color_button.setText(self.color.upper())

    def choose_files(self) -> None:
        names, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            self._source_dialog_dir(),
            "图片 (*.jpg *.jpeg *.png *.webp)",
        )
        if names:
            self._remember_source_dir(Path(names[0]).parent)
            self.add_files([Path(name) for name in names], remember_source=False)

    def choose_folder(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择图片文件夹", self._source_dialog_dir())
        if name:
            folder = Path(name)
            self._remember_source_dir(folder)
            self.add_files(images_in_folder(folder), remember_source=False)

    def _source_dialog_dir(self) -> str:
        saved = self.settings.value("source_dir", "", type=str)
        try:
            path = Path(saved)
            return str(path) if path.is_dir() else str(Path.home())
        except OSError:
            return str(Path.home())

    def _remember_source_dir(self, directory: Path) -> None:
        try:
            directory = directory.resolve()
            if not directory.is_dir():
                return
        except OSError:
            return
        self.settings.setValue("source_dir", str(directory))
        self.settings.sync()

    def choose_output(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_edit.text())
        if name:
            self.output_notice.hide()
            self.output_edit.setText(name)

    def add_files(self, paths: list[Path], remember_source: bool = True) -> None:
        if remember_source and paths:
            self._remember_source_dir(paths[0].parent)
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
        self.count_label.setText(f"共 {count} 张")
        self.file_actions.setVisible(bool(count))
        self.file_list.setVisible(bool(count))
        self.start_button.setText(f"开始处理 {count} 张图片" if count else "开始批量处理")
        self._update_start_button()

    def _update_start_button(self) -> None:
        output_valid = self._validate_output()
        text_valid = bool(self.text_input.text().strip())
        self.start_button.setEnabled(bool(self.sources and text_valid and output_valid and self.worker is None))
        if self.worker is not None:
            self.start_hint.setText("正在处理，请稍候")
        elif not self.sources:
            self.start_hint.setText("请先添加图片")
        elif not text_valid:
            self.start_hint.setText("请输入水印文字")
        elif not output_valid:
            self.start_hint.setText("请修正输出目录")
        else:
            self.start_hint.setText("参数就绪，可以开始处理")

    def _validate_output(self) -> bool:
        text = self.output_edit.text().strip()
        self.output_edit.setToolTip(text)
        directory_name = Path(text).name if text else ""
        self.output_button.setText(f"输出到：{directory_name or text}" if text else "选择输出目录")
        self.output_button.setToolTip(text or "选择输出目录")
        valid = bool(text)
        message = ""
        if valid:
            try:
                path = Path(text)
                if path.exists() and not path.is_dir():
                    valid, message = False, "输出路径不能是文件"
                else:
                    parent = path
                    while not parent.exists() and parent != parent.parent:
                        parent = parent.parent
                    if not parent.is_dir():
                        valid, message = False, "请选择有效的输出目录"
                    elif not os.access(parent, os.W_OK):
                        valid, message = False, "输出目录不可写"
            except OSError:
                valid, message = False, "输出目录格式无效"
        else:
            message = "请选择输出目录"
        self.output_edit.setProperty("error", not valid)
        self.output_edit.style().unpolish(self.output_edit)
        self.output_edit.style().polish(self.output_edit)
        self.output_button.setProperty("error", not valid)
        self.output_button.style().unpolish(self.output_button)
        self.output_button.style().polish(self.output_button)
        self.output_error.setText(message)
        self.output_error.setVisible(not valid)
        return valid

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
        if not self._validate_output():
            self.output_edit.setFocus()
            return
        if not self.start_button.isEnabled():
            return
        self._remember_current_text()
        output = Path(self.output_edit.text().strip()).resolve()
        self.output_dir = output
        self.progress.setRange(0, len(self.sources))
        self.progress.setValue(0)
        self.open_button.setEnabled(False)
        self.status_panel.show()
        self._set_status("处理中…")
        self.progress_count.setText(f"0 / {len(self.sources)}")
        self.worker = WatermarkWorker(self.sources.copy(), output, self.options())
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_completed)
        self.worker.finished.connect(self._worker_finished)
        self._update_start_button()
        self._set_inputs_enabled(False)
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
        ResultDialog(success, failed, self.output_dir, failures, self).exec()

    def _set_status(self, text: str, status: str = "") -> None:
        self.status.setText(text)
        self.status.setProperty("status", status)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def _worker_finished(self) -> None:
        self.worker = None
        self._set_inputs_enabled(True)
        self._update_start_button()

    def _set_inputs_enabled(self, enabled: bool) -> None:
        for widget in (
            self.preview,
            self.file_actions,
            self.file_list,
            self.text_input,
            self.font_size,
            self.opacity,
            self.color_button,
            self.position,
            self.margin,
            self.tiled,
            self.angle,
            self.spacing,
            self.output_edit,
            self.output_button,
            self.reset_button,
        ):
            widget.setEnabled(enabled)

    def stop_worker(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()

    def open_output(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        open_folder(self.output_dir)
