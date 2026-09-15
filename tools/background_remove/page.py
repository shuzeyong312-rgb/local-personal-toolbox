import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidgetItem, QPushButton, QSplitter, QVBoxLayout, QWidget

from app.icons import icon
from components.controls import AppComboBox
from components.dialogs import TaskDialog
from components.image_drop_list import ImageDropList
from components.preview_label import PreviewLabel
from services.image_background_remove import BackgroundRemoveOptions, remove_background
from tools.background_remove.worker import BackgroundRemoveWorker
from utils.image_files import images_in_folder


class BackgroundRemovePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[Path] = []
        self.worker: BackgroundRemoveWorker | None = None
        self.task_dialog: TaskDialog | None = None
        self.output_dir = Path.cwd() / "output"
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "LocalToolbox", "background_remove")
        self.preview_timer = QTimer(self, interval=120, singleShot=True)
        self.preview_timer.timeout.connect(self.update_preview)
        self._build_ui()
        self._restore_settings()
        self._connect_controls()
        self._update_file_state()

    def _build_ui(self) -> None:
        self.setObjectName("page")
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 14, 28, 20)
        root.setSpacing(6)
        root.addWidget(QLabel("白底转透明", objectName="pageTitle"))
        root.addWidget(QLabel("批量移除白色或浅色商品背景，生成透明 PNG。", objectName="pageSubtitle"))
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

    def _files_panel(self) -> QWidget:
        card, layout = self._card("图片预览")
        self.preview = PreviewLabel()
        self.preview.filesDropped.connect(self.add_files)
        self.preview.chooseFilesRequested.connect(self.choose_files)
        self.preview.chooseFolderRequested.connect(self.choose_folder)
        layout.addWidget(self.preview, 1)
        self.preview_state = AppComboBox()
        self.preview_state.addItem("处理后", "processed")
        self.preview_state.addItem("原图", "original")
        self.preview_state.setMaximumWidth(120)
        self.image_info = QLabel("", objectName="helperText")
        preview_row = QHBoxLayout()
        preview_row.addWidget(self.image_info, 1)
        preview_row.addWidget(self.preview_state)
        layout.addLayout(preview_row)
        self.warning = QLabel("", objectName="warningText")
        self.warning.hide()
        layout.addWidget(self.warning)
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
        card, layout = self._card("处理设置")
        self.settings_card = card
        self.mode = AppComboBox()
        for text, data in (("保守", "conservative"), ("标准", "standard"), ("强力", "strong")):
            self.mode.addItem(text, data)
        layout.addWidget(self._field("移除强度", self.mode))
        self.mode_hint = QLabel("适合大多数白底商品图，在背景去除和主体保留之间取得平衡。", objectName="helperText")
        self.mode_hint.setWordWrap(True)
        layout.addWidget(self.mode_hint)
        self.soften_edges = QCheckBox("柔化边缘")
        self.soften_edges.setChecked(True)
        layout.addWidget(self.soften_edges)
        layout.addWidget(QLabel("减少锯齿和白边，保留自然的渐变透明边缘。", objectName="helperText"))
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
        self.preview_state.currentIndexChanged.connect(self.schedule_preview)
        self.mode.currentIndexChanged.connect(self._mode_changed)
        self.soften_edges.toggled.connect(self.schedule_preview)
        self.output_edit.textChanged.connect(self._update_start_button)
        for signal in (self.mode.currentIndexChanged, self.soften_edges.toggled, self.output_edit.textChanged):
            signal.connect(self._save_settings)

    def _mode_changed(self, *_args) -> None:
        hints = {
            "conservative": "优先保留白色、银色和透明产品，去背景力度较弱。",
            "standard": "适合大多数白底商品图，在背景去除和主体保留之间取得平衡。",
            "strong": "适合浅灰或压缩杂色背景，可能误删与背景接近的浅色主体。",
        }
        self.mode_hint.setText(hints[self.mode.currentData()])
        self.schedule_preview()

    def options(self) -> BackgroundRemoveOptions:
        return BackgroundRemoveOptions(self.mode.currentData(), self.soften_edges.isChecked())

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
        accepted: list[Path] = []
        for path in paths:
            resolved = path.resolve()
            if resolved.is_file() and resolved.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and str(resolved).lower() not in known:
                self.sources.append(resolved)
                accepted.append(resolved)
                self.file_list.addItem(QListWidgetItem(resolved.name))
                known.add(str(resolved).lower())
        if accepted:
            self.settings.setValue("source_dir", str(accepted[0].parent))
        if self.sources and self.file_list.currentRow() < 0:
            self.file_list.setCurrentRow(0)
        self._update_file_state()
        self.schedule_preview()

    def clear_files(self) -> None:
        self.sources.clear()
        self.file_list.clear()
        self.preview.clear()
        self.image_info.clear()
        self.warning.hide()
        self._update_file_state()

    def _update_file_state(self) -> None:
        count = len(self.sources)
        self.count_label.setText(f"共 {count} 张")
        self.file_actions.setVisible(bool(count))
        self.file_list.setVisible(bool(count))
        self.preview_state.setVisible(bool(count))
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

    @staticmethod
    def _checkerboard(image: Image.Image) -> Image.Image:
        tile = 16
        board = Image.new("RGB", image.size, "#f4f4f4")
        draw = ImageDraw.Draw(board)
        for y in range(0, image.height, tile):
            for x in range(0, image.width, tile):
                if (x // tile + y // tile) % 2:
                    draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill="#d8d8d8")
        board.paste(image, mask=image.getchannel("A"))
        return board

    def update_preview(self) -> None:
        row = self.file_list.currentRow()
        if not 0 <= row < len(self.sources):
            return
        try:
            with Image.open(self.sources[row]) as original:
                original.load()
                image = ImageOps.exif_transpose(original).convert("RGBA")
                is_complex = False
                if self.preview_state.currentData() == "processed":
                    image, is_complex = remove_background(image, self.options())
                    image = self._checkerboard(image)
                image.thumbnail((900, 700), Image.Resampling.LANCZOS)
                self.preview.show_pixmap(QPixmap.fromImage(ImageQt(image)))
                self.image_info.setText(f"{original.width} × {original.height} px · {self.sources[row].name}")
                self.warning.setText("背景复杂，处理效果可能不理想")
                self.warning.setVisible(is_complex)
        except Exception as exc:
            self.preview.setText(f"预览失败：{exc}")

    def _save_settings(self, *_args) -> None:
        for key, value in {"mode": self.mode.currentData(), "soften_edges": self.soften_edges.isChecked(), "output_dir": self.output_edit.text().strip()}.items():
            self.settings.setValue(key, value)
        self.settings.sync()

    def _restore_settings(self) -> None:
        index = self.mode.findData(self.settings.value("mode", "standard", type=str))
        self.mode.setCurrentIndex(index if index >= 0 else 1)
        self.soften_edges.setChecked(self.settings.value("soften_edges", True, type=bool))
        output = Path(self.settings.value("output_dir", str(self.output_dir), type=str))
        self.output_edit.setText(str(output) if output.is_dir() else str(self.output_dir))
        self._mode_changed()

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
        self.worker = BackgroundRemoveWorker(self.sources.copy(), output, self.options())
        self.worker.current_file.connect(lambda name: self.task_dialog and self.task_dialog.status.setText(f"正在处理：{name}"))
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
