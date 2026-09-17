import sys

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app.icons import icon
from app.theme import STYLE
from app.title_bar import TitleBar
from tools.background_remove.page import BackgroundRemovePage
from tools.compression.page import CompressionPage
from tools.conversion.page import ConversionPage
from tools.resize.page import ResizePage
from tools.rename.page import RenamePage
from tools.order_calendar.page import OrderCalendarPage
from tools.competitor_monitor.product_view import CompetitorMonitorPage
from tools.watermark.page import WatermarkPage


class MainWindow(QMainWindow):
    RESIZE_MARGIN = 6
    NAVIGATION_SECTIONS = (
        ("图片工具", (("批量打水印", "stamp", 0), ("修改图片尺寸", "image", 1), ("白底转透明", "image", 2),
                     ("批量图片压缩", "image", 3), ("图片格式转换", "image", 4))),
        ("文件工具", (("批量重命名", "rename", 5),)),
        ("电商运营", (("出单日历", "calendar", 6), ("1688竞品监控", "monitor", 7))),
    )

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
        self.resize_page = ResizePage()
        self.background_remove_page = BackgroundRemovePage()
        self.compression_page = CompressionPage()
        self.conversion_page = ConversionPage()
        self.rename_page = RenamePage()
        self.order_calendar_page = OrderCalendarPage()
        self.competitor_monitor_page = CompetitorMonitorPage()
        self.pages.addWidget(self.watermark_page)
        self.pages.addWidget(self.resize_page)
        self.pages.addWidget(self.background_remove_page)
        self.pages.addWidget(self.compression_page)
        self.pages.addWidget(self.conversion_page)
        self.pages.addWidget(self.rename_page)
        self.pages.addWidget(self.order_calendar_page)
        self.pages.addWidget(self.competitor_monitor_page)
        self.navigation.currentItemChanged.connect(lambda current, _previous: self._activate_navigation(current))
        self._activate_navigation(self.navigation.currentItem())
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
        self.navigation = QListWidget(objectName="navigation")
        self.navigation.setIconSize(QSize(18, 18))
        first_item = None
        for title, entries in self.NAVIGATION_SECTIONS:
            section = QListWidgetItem(title)
            section.setFlags(Qt.ItemFlag.NoItemFlags)
            section.setForeground(QColor("#7F8DA3"))
            section.setSizeHint(QSize(180, 34))
            self.navigation.addItem(section)
            for label, icon_name, page_index in entries:
                item = QListWidgetItem(icon(icon_name, "#E2E8F0"), label)
                item.setData(Qt.ItemDataRole.UserRole, page_index)
                self.navigation.addItem(item)
                first_item = first_item or item
        self.navigation.setCurrentItem(first_item)
        column.addWidget(self.navigation)
        column.addWidget(QLabel("本地处理 · 数据不上传", objectName="privacy"))
        return sidebar

    def _activate_navigation(self, item: QListWidgetItem | None) -> None:
        if item and item.data(Qt.ItemDataRole.UserRole) is not None and hasattr(self, "pages"):
            self.pages.setCurrentIndex(item.data(Qt.ItemDataRole.UserRole))

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
        self.resize_page.stop_worker()
        self.background_remove_page.stop_worker()
        self.compression_page.stop_worker()
        self.conversion_page.stop_worker()
        self.rename_page.stop_worker()
        self.competitor_monitor_page.stop_worker()
        self.competitor_monitor_page.store.close()
        super().closeEvent(event)


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("本地个人工具箱")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    return app.exec()
