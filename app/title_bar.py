from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from app.icons import icon


class TitleBar(QWidget):
    HEIGHT = 48

    def __init__(self, window) -> None:
        super().__init__(objectName="titleBar")
        self.host_window = window
        self.setFixedHeight(self.HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()
        minimize = QPushButton(objectName="windowButton")
        self.maximize = QPushButton(objectName="windowButton")
        close = QPushButton(objectName="closeButton")
        for button in (minimize, self.maximize, close):
            button.setIconSize(QSize(16, 16))
        minimize.setIcon(icon("minimize", "#334155", 16))
        self.maximize.setIcon(icon("maximize", "#334155", 15))
        close.setIcon(icon("close", "#334155", 16))
        minimize.setToolTip("最小化")
        self.maximize.setToolTip("最大化")
        close.setToolTip("关闭")
        minimize.clicked.connect(window.showMinimized)
        self.maximize.clicked.connect(self.toggle_maximized)
        close.clicked.connect(window.close)
        layout.addWidget(minimize)
        layout.addWidget(self.maximize)
        layout.addWidget(close)

    def toggle_maximized(self) -> None:
        self.host_window.showNormal() if self.host_window.isMaximized() else self.host_window.showMaximized()
        self.update_state()

    def update_state(self) -> None:
        name = "restore" if self.host_window.isMaximized() else "maximize"
        self.maximize.setIcon(icon(name, "#334155", 15))
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
