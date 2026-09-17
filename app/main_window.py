import sys

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.dashboard_page import DashboardPage
from app.icons import icon
from app.theme import STYLE
from app.title_bar import TitleBar
from app.tool_registry import TOOL_REGISTRY, TOOLS_BY_ID, dock_tools, tools_in_category
from app.widgets.dashboard import AmbientBackground, BrandMark, TOOL_ACCENTS
from app.widgets.dashboard_theme import DASHBOARD_STYLE


class MainWindow(QMainWindow):
    RESIZE_MARGIN = 6
    CATEGORIES = ("图片工具", "文件工具", "电商运营")

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Personal Toolbox")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.resize(1240, 820)
        self.setMinimumSize(1080, 700)

        root = AmbientBackground(objectName="appRoot")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._sidebar())

        main = QWidget(objectName="mainArea")
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 21)
        main_layout.setSpacing(0)
        self.title_bar = TitleBar(self)
        self.title_bar.searchChanged.connect(self._filter_dashboard)
        self.title_bar.backRequested.connect(self.show_dashboard)
        main_layout.addWidget(self.title_bar)

        self.pages = QStackedWidget(objectName="mainStack")
        self.dashboard_page = DashboardPage(self.open_tool)
        self.pages.addWidget(self.dashboard_page)
        self.tool_pages = {tool.id: tool.page_factory() for tool in TOOL_REGISTRY}
        for tool in TOOL_REGISTRY:
            self.pages.addWidget(self.tool_pages[tool.id])
        self.watermark_page = self.tool_pages["watermark"]
        self.resize_page = self.tool_pages["resize"]
        self.background_remove_page = self.tool_pages["background_remove"]
        self.compression_page = self.tool_pages["compression"]
        self.conversion_page = self.tool_pages["conversion"]
        self.rename_page = self.tool_pages["rename"]
        self.order_calendar_page = self.tool_pages["order_calendar"]
        self.competitor_monitor_page = self.tool_pages["competitor_monitor"]
        main_layout.addWidget(self.pages, 1)

        self.dock = self._floating_dock()
        main_layout.addWidget(self.dock, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(main, 1)
        self.setCentralWidget(root)
        QApplication.instance().installEventFilter(self)
        self.show_dashboard()

    def _sidebar(self) -> QWidget:
        sidebar = QWidget(objectName="sidebar")
        sidebar.setFixedWidth(224)
        column = QVBoxLayout(sidebar)
        column.setContentsMargins(14, 18, 14, 14)
        column.setSpacing(0)

        brand_box = QWidget(objectName="brandBox")
        brand_layout = QHBoxLayout(brand_box)
        brand_layout.setContentsMargins(6, 2, 5, 25)
        brand_layout.setSpacing(11)
        brand_layout.addWidget(BrandMark())
        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        brand_text.addWidget(QLabel("Personal Toolbox", objectName="brand"))
        brand_text.addWidget(QLabel("本地个人工作空间", objectName="brandHint"))
        brand_layout.addLayout(brand_text)
        brand_layout.addStretch()
        column.addWidget(brand_box)

        self.navigation = QListWidget(objectName="navigation")
        self.navigation.setIconSize(QSize(18, 18))
        self.navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._navigation_items: dict[str, QListWidgetItem] = {}
        dashboard_item = QListWidgetItem(icon("home", "#71809C"), "所有工具")
        dashboard_item.setData(Qt.ItemDataRole.UserRole, "dashboard")
        self.navigation.addItem(dashboard_item)
        self._navigation_items["dashboard"] = dashboard_item

        for category in self.CATEGORIES:
            self._add_navigation_section(category, len(tools_in_category(category)))
            for tool in tools_in_category(category):
                accent = TOOL_ACCENTS[tool.id][0]
                item = QListWidgetItem(icon(tool.icon, accent, 18), tool.name)
                item.setData(Qt.ItemDataRole.UserRole, tool.id)
                self.navigation.addItem(item)
                self._navigation_items[tool.id] = item

        self.navigation.currentItemChanged.connect(lambda current, _previous: self._activate_navigation(current))
        column.addWidget(self.navigation, 1)

        privacy = QFrame(objectName="privacyCard")
        privacy_layout = QHBoxLayout(privacy)
        privacy_layout.setContentsMargins(11, 11, 10, 11)
        privacy_layout.setSpacing(9)
        privacy_icon = QLabel("●", objectName="privacyIcon")
        privacy_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        privacy_layout.addWidget(privacy_icon)
        copy = QVBoxLayout()
        copy.setSpacing(1)
        copy.addWidget(QLabel("本地处理", objectName="privacyTitle"))
        copy.addWidget(QLabel("数据不会离开设备", objectName="privacyHint"))
        privacy_layout.addLayout(copy, 1)
        privacy_layout.addWidget(QLabel("→", objectName="privacyArrow"))
        column.addWidget(privacy)
        column.addWidget(QLabel("Personal Toolbox", objectName="sidebarVersion"), 0, Qt.AlignmentFlag.AlignHCenter)
        return sidebar

    def _add_navigation_section(self, category: str, count: int) -> None:
        item = QListWidgetItem(category)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setForeground(QBrush(Qt.GlobalColor.transparent))
        item.setSizeHint(QSize(180, 31))
        self.navigation.addItem(item)
        row = QWidget(objectName="sidebarSection")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(9, 8, 8, 2)
        row_layout.setSpacing(6)
        row_layout.addWidget(QLabel(category, objectName="sidebarSectionLabel"))
        row_layout.addStretch(1)
        row_layout.addWidget(QLabel(str(count), objectName="sidebarSectionCount"))
        self.navigation.setItemWidget(item, row)

    def _floating_dock(self) -> QFrame:
        dock = QFrame(objectName="floatingDock")
        dock.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        dock.setMinimumWidth(390)
        dock.setMaximumWidth(520)
        shadow = QGraphicsDropShadowEffect(dock)
        shadow.setBlurRadius(34)
        shadow.setOffset(0, 7)
        shadow.setColor(QColor(44, 65, 105, 24))
        dock.setGraphicsEffect(shadow)
        dock_layout = QHBoxLayout(dock)
        dock_layout.setContentsMargins(11, 7, 11, 7)
        dock_layout.setSpacing(7)
        dock_layout.addStretch(1)

        home = self._dock_button("首页", "home", "#FFFFFF", active=True)
        home.clicked.connect(self.show_dashboard)
        dock_layout.addWidget(home)
        for tool in dock_tools():
            button = self._dock_button(tool.name, tool.icon, TOOL_ACCENTS[tool.id][0])
            button.clicked.connect(lambda _checked=False, tool_id=tool.id: self.open_tool(tool_id))
            dock_layout.addWidget(button)
        dock_layout.addStretch(1)
        return dock

    @staticmethod
    def _dock_button(label: str, icon_name: str, icon_color: str, active: bool = False) -> QToolButton:
        button = QToolButton(objectName="dockButton")
        button.setProperty("active", active)
        button.setIcon(icon(icon_name, icon_color, 18))
        button.setIconSize(QSize(18, 18))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(label)
        button.setFixedSize(40, 40)
        return button

    def _activate_navigation(self, item: QListWidgetItem | None) -> None:
        if not item:
            return
        page_id = item.data(Qt.ItemDataRole.UserRole)
        if page_id == "dashboard":
            self._show_dashboard()
        elif page_id in TOOLS_BY_ID:
            self._show_tool(page_id)

    def _select_navigation(self, page_id: str) -> None:
        self.navigation.blockSignals(True)
        self.navigation.setCurrentItem(self._navigation_items[page_id])
        self.navigation.blockSignals(False)

    def show_dashboard(self) -> None:
        self._select_navigation("dashboard")
        self._show_dashboard()

    def _show_dashboard(self) -> None:
        self.pages.setCurrentWidget(self.dashboard_page)
        self.title_bar.show_dashboard()
        self.dock.show()

    def open_tool(self, tool_id: str) -> None:
        if tool_id not in TOOLS_BY_ID:
            return
        self._select_navigation(tool_id)
        self._show_tool(tool_id)

    def _show_tool(self, tool_id: str) -> None:
        self.pages.setCurrentWidget(self.tool_pages[tool_id])
        self.title_bar.show_tool(TOOLS_BY_ID[tool_id])
        self.dock.hide()

    def _filter_dashboard(self, query: str) -> None:
        self.dashboard_page.filter_tools(query)
        if self.pages.currentWidget() is self.dashboard_page:
            self._show_dashboard()

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
    app.setApplicationName("Personal Toolbox")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE + DASHBOARD_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()
