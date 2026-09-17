import sys

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.dashboard_page import DashboardPage
from app.dashboard_theme import SIDEBAR_STYLE
from app.icons import dashboard_icon
from app.theme import STYLE
from app.title_bar import TitleBar
from app.tool_registry import CATEGORY_ORDER, tools_for_category
from app.widgets.dashboard import AmbientBackground, BrandMark
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

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("本地个人工具箱")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.resize(1240, 820)
        self.setMinimumSize(1080, 700)

        root = AmbientBackground()
        root.setStyleSheet(SIDEBAR_STYLE)
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
        self.dashboard_page = DashboardPage()
        self.watermark_page = WatermarkPage()
        self.resize_page = ResizePage()
        self.background_remove_page = BackgroundRemovePage()
        self.compression_page = CompressionPage()
        self.conversion_page = ConversionPage()
        self.rename_page = RenamePage()
        self.order_calendar_page = OrderCalendarPage()
        self.competitor_monitor_page = CompetitorMonitorPage()

        self.pages.addWidget(self.dashboard_page)
        for page in (
            self.watermark_page,
            self.resize_page,
            self.background_remove_page,
            self.compression_page,
            self.conversion_page,
            self.rename_page,
            self.order_calendar_page,
            self.competitor_monitor_page,
        ):
            self.pages.addWidget(page)

        self.dashboard_page.toolActivated.connect(self._show_tool)
        self.pages.setCurrentIndex(0)
        self._set_nav_checked(None)
        main_layout.addWidget(self.pages, 1)
        layout.addWidget(main, 1)
        self.setCentralWidget(root)
        QApplication.instance().installEventFilter(self)

    def _sidebar(self) -> QWidget:
        sidebar = QWidget(objectName="toolboxSidebar")
        sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sidebar.setFixedWidth(238)
        column = QVBoxLayout(sidebar)
        column.setContentsMargins(16, 48, 14, 14)
        column.setSpacing(0)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(4, 0, 0, 0)
        brand_row.setSpacing(10)
        brand_row.addWidget(BrandMark())
        brand_copy = QVBoxLayout()
        brand_copy.setSpacing(1)
        brand_copy.addWidget(QLabel("Personal Toolbox", objectName="sidebarBrand"))
        brand_copy.addWidget(QLabel("本地个人工作空间", objectName="sidebarBrandHint"))
        brand_row.addLayout(brand_copy, 1)
        column.addLayout(brand_row)
        column.addSpacing(30)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self._nav_buttons: dict[int | None, QPushButton] = {}

        home = self._nav_button("首页", "home", "#3478F6")
        home.clicked.connect(self._show_dashboard)
        self._nav_buttons[None] = home
        self.nav_group.addButton(home)
        column.addWidget(home)
        column.addSpacing(22)

        for category in CATEGORY_ORDER:
            section_row = QWidget()
            section_layout = QHBoxLayout(section_row)
            section_layout.setContentsMargins(10, 0, 8, 6)
            section_layout.setSpacing(6)
            section_layout.addWidget(QLabel(category, objectName="sidebarSection"))
            section_layout.addStretch(1)
            section_layout.addWidget(QLabel(str(len(tools_for_category(category))), objectName="sidebarCount"))
            column.addWidget(section_row)

            for spec in tools_for_category(category):
                button = self._nav_button(spec.name, spec.icon_name, spec.accent)
                button.clicked.connect(lambda _checked=False, page=spec.page_index: self._show_tool(page))
                self._nav_buttons[spec.page_index] = button
                self.nav_group.addButton(button)
                column.addWidget(button)
            column.addSpacing(14)

        column.addStretch(1)
        column.addWidget(self._privacy_card())
        column.addSpacing(10)
        version = QLabel("LOCAL · v1", objectName="versionLabel")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(version)
        return sidebar

    @staticmethod
    def _nav_button(label: str, icon_name: str, accent: str) -> QPushButton:
        button = QPushButton(label, objectName="sidebarItem")
        button.setCheckable(True)
        button.setIcon(dashboard_icon(icon_name, accent, 17))
        button.setIconSize(QSize(17, 17))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    @staticmethod
    def _privacy_card() -> QWidget:
        card = QWidget(objectName="privacyCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 11, 10, 11)
        row.setSpacing(9)
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setPixmap(dashboard_icon("shield", "#5A7BAA", 18).pixmap(18, 18))
        row.addWidget(icon_label)
        copy = QVBoxLayout()
        copy.setSpacing(1)
        copy.addWidget(QLabel("本地处理", objectName="privacyTitle"))
        copy.addWidget(QLabel("数据不会离开设备。", objectName="privacyHint"))
        row.addLayout(copy, 1)
        arrow = QLabel("›")
        arrow.setStyleSheet("color:#A3AFC1; background:transparent; font-size:18px;")
        row.addWidget(arrow)
        return card

    def _set_nav_checked(self, page_index: int | None) -> None:
        button = self._nav_buttons.get(page_index)
        if button is not None:
            button.setChecked(True)

    def _show_dashboard(self) -> None:
        self.pages.setCurrentIndex(0)
        self._set_nav_checked(None)

    def _show_tool(self, page_index: int) -> None:
        if page_index not in self._nav_buttons:
            return
        self.dashboard_page.record_recent(page_index)
        self.pages.setCurrentIndex(page_index + 1)
        self._set_nav_checked(page_index)

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
