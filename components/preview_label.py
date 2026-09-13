from pathlib import Path

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QLabel

from app.icons import icon
from utils.image_files import images_in_folder, is_supported_image


class PreviewLabel(QLabel):
    filesDropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self._pixmap = QPixmap()
        self.setObjectName("preview")
        self.setProperty("dropActive", False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(360, 380)
        self.setAcceptDrops(True)

    def show_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self._rescale()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rescale()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self._pixmap.isNull():
            return
        painter = QPainter(self)
        center = self.rect().center()
        pixmap = icon("image", "#94A3B8", 30).pixmap(30, 30)
        painter.drawPixmap(QPoint(center.x() - 15, center.y() - 48), pixmap)
        painter.setPen(QColor("#475569"))
        painter.drawText(self.rect().adjusted(0, 12, 0, 0), Qt.AlignmentFlag.AlignCenter, "选择或拖入图片")
        painter.setPen(QColor("#94A3B8"))
        painter.drawText(self.rect().adjusted(0, 54, 0, 0), Qt.AlignmentFlag.AlignCenter, "支持 JPG · PNG · WEBP")

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
        super().clear()
        self.update()
