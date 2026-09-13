import sys

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app.icons import icon
from app.theme import STYLE
from app.title_bar import TitleBar
from tools.watermark.page import WatermarkPage


class MainWindow(QMainWindow):
    RESIZE_MARGIN = 6

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("本地个人工具箱")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.resize(1240, 820)
        self.setMinimumSize(1080, 700)

        root = QWidget(objectName="appRoot")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._sidebar())

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)
        self.pages = QStackedWidget()
        self.watermark_page = WatermarkPage()
        self.pages.addWidget(self.watermark_page)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        main_layout.addWidget(self.pages, 1)
        layout.addWidget(main, 1)
        self.setCentralWidget(root)
        QApplication.instance().installEventFilter(self)

    def _sidebar(self) -> QWidget:
        sidebar = QWidget(objectName="sidebar")
        sidebar.setFixedWidth(220)
        column = QVBoxLayout(sidebar)
        column.setContentsMargins(0, 0, 0, 12)
        column.setSpacing(0)
        brand_box = QWidget()
        brand_layout = QVBoxLayout(brand_box)
        brand_layout.setContentsMargins(20, 22, 20, 20)
        brand_layout.setSpacing(2)
        brand_layout.addWidget(QLabel("个人工具箱", objectName="brand"))
        brand_layout.addWidget(QLabel("LOCAL TOOLBOX", objectName="brandHint"))
        column.addWidget(brand_box)
        column.addWidget(QLabel("图片工具", objectName="sidebarSection"))
        self.navigation = QListWidget(objectName="navigation")
        self.navigation.setIconSize(QSize(18, 18))
        self.navigation.addItem(QListWidgetItem(icon("stamp", "#E2E8F0"), "批量打水印"))
        self.navigation.setCurrentRow(0)
        column.addWidget(self.navigation)
        column.addWidget(QLabel("本地处理 · 数据不上传", objectName="privacy"))
        return sidebar

    def event(self, event) -> bool:
        if event.type() == QEvent.Type.WindowStateChange and hasattr(self, "title_bar"):
            self.title_bar.update_state()
        return super().event(event)

    def eventFilter(self, watched, event) -> bool:
        if not isinstance(watched, QWidget) or watched.window() is not self or self.isMaximized():
            return super().eventFilter(watched, event)
        if event.type() not in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress):
            return super().eventFilter(watched, event)
        edges = self._resize_edges(event.globalPosition().toPoint())
        if event.type() == QEvent.Type.MouseMove and not event.buttons():
            self.setCursor(self._resize_cursor(edges))
        elif event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton and edges:
            self.windowHandle().startSystemResize(edges)
            return True
        return super().eventFilter(watched, event)

    def _resize_edges(self, global_pos):
        pos = self.mapFromGlobal(global_pos)
        edges = Qt.Edge(0)
        if pos.x() <= self.RESIZE_MARGIN:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() >= self.width() - self.RESIZE_MARGIN:
            edges |= Qt.Edge.RightEdge
        if pos.y() <= self.RESIZE_MARGIN:
            edges |= Qt.Edge.TopEdge
        elif pos.y() >= self.height() - self.RESIZE_MARGIN:
            edges |= Qt.Edge.BottomEdge
        return edges

    @staticmethod
    def _resize_cursor(edges):
        if edges in (Qt.Edge.LeftEdge | Qt.Edge.TopEdge, Qt.Edge.RightEdge | Qt.Edge.BottomEdge):
            return QCursor(Qt.CursorShape.SizeFDiagCursor)
        if edges in (Qt.Edge.RightEdge | Qt.Edge.TopEdge, Qt.Edge.LeftEdge | Qt.Edge.BottomEdge):
            return QCursor(Qt.CursorShape.SizeBDiagCursor)
        if edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge):
            return QCursor(Qt.CursorShape.SizeHorCursor)
        if edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge):
            return QCursor(Qt.CursorShape.SizeVerCursor)
        return QCursor(Qt.CursorShape.ArrowCursor)

    def closeEvent(self, event) -> None:
        self.watermark_page.stop_worker()
        super().closeEvent(event)


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("本地个人工具箱")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    return app.exec()
