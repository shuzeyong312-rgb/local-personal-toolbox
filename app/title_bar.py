from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from app.icons import icon


class TitleBar(QWidget):
    HEIGHT = 36

    def __init__(self, window) -> None:
        super().__init__(objectName="chromeTitleBar")
        self.host_window = window
        self.setFixedHeight(self.HEIGHT)
        self.setStyleSheet(
            """
            QWidget#chromeTitleBar { background: transparent; }
            QPushButton#chromeButton, QPushButton#chromeCloseButton {
                min-width: 44px; max-width: 44px;
                min-height: 36px; max-height: 36px;
                padding: 0; border: 0; border-radius: 0;
                background: transparent;
            }
            QPushButton#chromeButton:hover { background: rgba(225, 232, 242, 150); }
            QPushButton#chromeCloseButton:hover { background: #E81123; }
            """
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()

        minimize = QPushButton(objectName="chromeButton")
        self.maximize = QPushButton(objectName="chromeButton")
        close = QPushButton(objectName="chromeCloseButton")
        for button in (minimize, self.maximize, close):
            button.setIconSize(QSize(15, 15))
        minimize.setIcon(icon("minimize", "#5E6B80", 15))
        self.maximize.setIcon(icon("maximize", "#5E6B80", 14))
        close.setIcon(icon("close", "#5E6B80", 15))
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
        self.maximize.setIcon(icon(name, "#5E6B80", 14))
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
