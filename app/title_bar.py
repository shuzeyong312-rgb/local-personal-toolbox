from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.icons import icon
from app.tool_registry import ToolDefinition


class TitleBar(QWidget):
    searchChanged = Signal(str)
    backRequested = Signal()
    HEIGHT = 78

    def __init__(self, window) -> None:
        super().__init__(objectName="titleBar")
        self.host_window = window
        self.setFixedHeight(self.HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(38, 14, 0, 10)
        layout.setSpacing(10)

        self.back = QPushButton(objectName="headerBackButton")
        self.back.setIcon(icon("arrow-left", "#526175", 18))
        self.back.setIconSize(QSize(18, 18))
        self.back.setToolTip("返回所有工具")
        self.back.clicked.connect(self.backRequested)
        layout.addWidget(self.back)

        self.detail_titles = QWidget(objectName="detailTitles")
        detail_layout = QVBoxLayout(self.detail_titles)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(1)
        self.detail_name = QLabel(objectName="headerTitle")
        self.detail_description = QLabel(objectName="headerDescription")
        detail_layout.addWidget(self.detail_name)
        detail_layout.addWidget(self.detail_description)
        layout.addWidget(self.detail_titles)

        self.search_shell = QFrame(objectName="globalSearchShell")
        search_layout = QHBoxLayout(self.search_shell)
        search_layout.setContentsMargins(16, 0, 12, 0)
        search_layout.setSpacing(9)
        search_icon = QLabel(objectName="searchIcon")
        search_icon.setPixmap(icon("search", "#71809C", 18).pixmap(18, 18))
        search_layout.addWidget(search_icon)
        self.search = QLineEdit(objectName="globalSearch")
        self.search.setPlaceholderText("搜索工具、输入关键词或命令...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.searchChanged)
        search_layout.addWidget(self.search, 1)
        self.shortcut_badge = QLabel("Ctrl K", objectName="searchShortcutBadge")
        search_layout.addWidget(self.shortcut_badge)
        layout.addWidget(self.search_shell, 1)

        for name, tooltip in (("sun", "外观设置（即将提供）"), ("bell", "通知（即将提供）")):
            action = QPushButton(objectName="headerAction")
            action.setIcon(icon(name, "#6E7C91", 17))
            action.setIconSize(QSize(17, 17))
            action.setToolTip(tooltip)
            action.setEnabled(False)
            layout.addWidget(action)
        profile = QPushButton(objectName="profileAction")
        profile.setIcon(icon("user", "#73839B", 17))
        profile.setIconSize(QSize(17, 17))
        profile.setToolTip("本地个人工作空间")
        profile.setEnabled(False)
        layout.addWidget(profile)

        minimize = QPushButton(objectName="windowButton")
        self.maximize = QPushButton(objectName="windowButton")
        close = QPushButton(objectName="closeButton")
        for button in (minimize, self.maximize, close):
            button.setIconSize(QSize(16, 16))
        minimize.setIcon(icon("minimize", "#526175", 16))
        self.maximize.setIcon(icon("maximize", "#526175", 15))
        close.setIcon(icon("close", "#526175", 16))
        minimize.setToolTip("最小化")
        self.maximize.setToolTip("最大化")
        close.setToolTip("关闭")
        minimize.clicked.connect(window.showMinimized)
        self.maximize.clicked.connect(self.toggle_maximized)
        close.clicked.connect(window.close)
        layout.addWidget(minimize)
        layout.addWidget(self.maximize)
        layout.addWidget(close)

        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), window)
        self.search_shortcut.activated.connect(self.focus_search)
        self.show_dashboard()

    def focus_search(self) -> None:
        if not self.search_shell.isVisible():
            self.backRequested.emit()
        self.search.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search.selectAll()

    def show_dashboard(self) -> None:
        self.back.hide()
        self.detail_titles.hide()
        self.search_shell.show()

    def show_tool(self, tool: ToolDefinition) -> None:
        self.search_shell.hide()
        self.back.show()
        self.detail_name.setText(tool.name)
        self.detail_description.setText(tool.description)
        self.detail_titles.show()

    def toggle_maximized(self) -> None:
        self.host_window.showNormal() if self.host_window.isMaximized() else self.host_window.showMaximized()
        self.update_state()

    def update_state(self) -> None:
        name = "restore" if self.host_window.isMaximized() else "maximize"
        self.maximize.setIcon(icon(name, "#526175", 15))
        self.maximize.setToolTip("还原" if self.host_window.isMaximized() else "最大化")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.host_window.windowHandle().startSystemMove()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximized()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
