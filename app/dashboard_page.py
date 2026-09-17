from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from app.icons import icon
from app.tool_registry import TOOL_REGISTRY, ToolDefinition


class ToolCard(QToolButton):
    def __init__(self, tool: ToolDefinition) -> None:
        super().__init__(objectName="toolCard")
        self.tool = tool
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(190 if tool.card_size == "large" else 150)
        self.setToolTip(f"打开{tool.name}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 17, 18, 16)
        layout.setSpacing(10)
        header = QHBoxLayout()
        header.setSpacing(8)
        icon_label = QLabel(objectName="toolCardIcon")
        icon_label.setPixmap(icon(tool.icon, "#2563EB", 18).pixmap(18, 18))
        header.addWidget(icon_label)
        header.addWidget(QLabel(tool.category, objectName="toolCardCategory"))
        header.addStretch()
        header.addWidget(QLabel("↗", objectName="toolCardArrow"))
        layout.addLayout(header)
        layout.addWidget(QLabel(tool.name, objectName="toolCardTitle"))
        description = QLabel(tool.description, objectName="toolCardDescription")
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addStretch()
        layout.addWidget(self._preview())

    def _preview(self) -> QWidget:
        preview = QFrame(objectName="toolPreview")
        layout = QHBoxLayout(preview)
        layout.setContentsMargins(11, 8, 11, 8)
        layout.setSpacing(7)
        labels = {
            "watermark": ("TEXT", "TEXT", "文字水印"),
            "resize": ("1200", "→", "800 px"),
            "background_remove": ("□", "●", "透明 PNG"),
            "compression": ("4.8 MB", "↓", "2.1 MB"),
            "conversion": ("JPG", "→", "PNG"),
            "rename": ("IMG_01", "…", "详情页_01"),
            "order_calendar": ("09", "17", "待评价"),
            "competitor_monitor": ("¥45", "→", "¥50"),
        }[self.tool.id]
        for index, text in enumerate(labels):
            label = QLabel(text, objectName="toolPreviewValue" if index != 1 else "toolPreviewArrow")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label, 1 if index != 1 else 0)
        return preview


class DashboardPage(QWidget):
    _BENTO_POSITIONS = {
        "watermark": (0, 0, 1, 2), "resize": (0, 2, 1, 1),
        "background_remove": (1, 0, 1, 1), "compression": (1, 1, 1, 1), "conversion": (1, 2, 1, 1),
        "order_calendar": (2, 0, 1, 1), "rename": (2, 1, 1, 1), "competitor_monitor": (2, 2, 1, 1),
    }

    def __init__(self, open_tool: Callable[[str], None]) -> None:
        super().__init__(objectName="dashboardPage")
        self._open_tool = open_tool
        self.cards = {tool.id: ToolCard(tool) for tool in TOOL_REGISTRY}
        for tool_id, card in self.cards.items():
            card.clicked.connect(lambda _checked=False, current=tool_id: self._open_tool(current))
        self._build_ui()
        self._populate_bento()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(objectName="dashboardScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(objectName="dashboardContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 26, 32, 18)
        layout.setSpacing(18)
        title_row = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(4)
        titles.addWidget(QLabel("所有工具", objectName="dashboardTitle"))
        titles.addWidget(QLabel("需要的工具，都在这里。", objectName="dashboardSubtitle"))
        title_row.addLayout(titles)
        title_row.addStretch()
        title_row.addWidget(QLabel(f"{len(TOOL_REGISTRY)} 个工具", objectName="toolCount"))
        layout.addLayout(title_row)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        for column in range(3):
            self.grid.setColumnStretch(column, 1)
        layout.addWidget(self.grid_host)
        self.empty = QLabel("没有找到匹配的工具", objectName="dashboardEmpty")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.hide()
        layout.addWidget(self.empty)
        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def filter_tools(self, query: str) -> None:
        normalized = query.strip().casefold()
        tools = tuple(tool for tool in TOOL_REGISTRY if not normalized or normalized in " ".join((tool.name, tool.description, tool.category)).casefold())
        self._clear_grid()
        if normalized:
            for index, tool in enumerate(tools):
                card = self.cards[tool.id]
                card.show()
                self.grid.addWidget(card, index // 3, index % 3)
        else:
            self._populate_bento()
        self.empty.setVisible(not tools)

    def _clear_grid(self) -> None:
        while self.grid.count():
            self.grid.takeAt(0)
        for card in self.cards.values():
            card.hide()

    def _populate_bento(self) -> None:
        self._clear_grid()
        for tool in TOOL_REGISTRY:
            row, column, row_span, column_span = self._BENTO_POSITIONS[tool.id]
            card = self.cards[tool.id]
            card.show()
            self.grid.addWidget(card, row, column, row_span, column_span)
