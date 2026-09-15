from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QListWidget

from utils.image_files import is_supported_image


class ImageDropList(QListWidget):
    filesDropped = Signal(list)

    def __init__(self, extensions: set[str] | None = None) -> None:
        super().__init__()
        self.extensions = extensions
        self.setObjectName("dropList")
        self.setAcceptDrops(True)
        self.setMinimumHeight(130)
        self.setToolTip("可将 JPG、JPEG、PNG、WEBP 图片拖到这里")

    def _supported(self, path: Path) -> bool:
        return path.is_file() and (path.suffix.lower() in self.extensions if self.extensions else is_supported_image(path))

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setPen(QColor("#74839a"))
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, "拖拽图片或文件夹到这里\n支持 JPG · PNG · WEBP")

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        files: list[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_dir():
                files.extend(p for p in path.rglob("*") if self._supported(p))
            elif self._supported(path):
                files.append(path)
        if files:
            self.filesDropped.emit(files)
        event.acceptProposedAction()
