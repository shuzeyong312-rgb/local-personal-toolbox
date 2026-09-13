from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.icons import icon
from utils.image_files import images_in_folder, is_supported_image


class PreviewLabel(QLabel):
    filesDropped = Signal(list)
    chooseFilesRequested = Signal()
    chooseFolderRequested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._pixmap = QPixmap()
        self.setObjectName("preview")
        self.setProperty("dropActive", False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(360, 380)
        self.setAcceptDrops(True)
        self.empty_state = QWidget(self, objectName="previewEmpty")
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(6)
        image = QLabel()
        image.setPixmap(icon("image", "#8A99AE", 32).pixmap(32, 32))
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(image)
        empty_layout.addWidget(QLabel("拖入图片，或点击添加", objectName="emptyTitle"), alignment=Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(QLabel("支持 JPG、PNG、WEBP", objectName="emptyHint"), alignment=Qt.AlignmentFlag.AlignCenter)
        empty_layout.addSpacing(8)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        add_files = QPushButton("添加图片", objectName="primary")
        add_files.setIcon(icon("plus", "#FFFFFF"))
        add_folder = QPushButton("添加文件夹")
        add_folder.setIcon(icon("folder"))
        add_files.clicked.connect(self.chooseFilesRequested)
        add_folder.clicked.connect(self.chooseFolderRequested)
        buttons.addWidget(add_files)
        buttons.addWidget(add_folder)
        empty_layout.addLayout(buttons)

    def show_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.empty_state.hide()
        self._rescale()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.empty_state.setGeometry(self.contentsRect())
        self._rescale()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            self._set_drop_active(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._set_drop_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        paths: list[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            paths.extend(images_in_folder(path) if path.is_dir() else ([path] if is_supported_image(path) else []))
        self._set_drop_active(False)
        if paths:
            self.filesDropped.emit(paths)
        event.acceptProposedAction()

    def _set_drop_active(self, active: bool) -> None:
        self.setProperty("dropActive", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _rescale(self) -> None:
        if not self._pixmap.isNull():
            size = self.contentsRect().size()
            self.setPixmap(self._pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def clear(self) -> None:
        self._pixmap = QPixmap()
        self.empty_state.show()
        super().clear()
        self.update()
