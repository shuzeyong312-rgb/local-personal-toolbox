from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from app.icons import icon
from app.tool_registry import TOOL_REGISTRY, ToolDefinition


class ToolCard(QToolButton):
    _ICON_COLORS = {
        "图片工具": ("#2563EB", "#EBF3FF"),
        "文件工具": ("#7C5CE0", "#F1EEFF"),
        "电商运营": ("#12966F", "#EAF8F3"),
    }

    def __init__(self, tool: ToolDefinition) -> None:
        super().__init__(objectName="toolCard")
        self.tool = tool
        self.setProperty("size", tool.card_size)
        self.setProperty("featured", tool.featured)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight({"large": 254, "medium": 122, "small": 112}[tool.card_size])
        self.setToolTip(f"打开{tool.name}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 15, 16, 14)
        layout.setSpacing(6)
        header = QHBoxLayout()
        header.setSpacing(8)
        icon_color, icon_background = self._ICON_COLORS[tool.category]
        icon_label = QLabel(objectName="toolCardIcon")
        icon_label.setProperty("category", tool.category)
        icon_label.setPixmap(icon(tool.icon, icon_color, 18).pixmap(18, 18))
        icon_label.setStyleSheet(f"background: {icon_background};")
        header.addWidget(icon_label)
        header.addWidget(QLabel(tool.category, objectName="toolCardCategory"))
        header.addStretch()
        header.addWidget(QLabel("↗", objectName="toolCardArrow"))
        layout.addLayout(header)
        layout.addWidget(QLabel(tool.name, objectName="toolCardTitle"))
        description = QLabel(tool.description, objectName="toolCardDescription")
        description.setWordWrap(True)
        description.setMaximumHeight(32)
        layout.addWidget(description)
        layout.addStretch(1)
        preview = self._preview()
        preview.setFixedHeight({"large": 70, "medium": 56, "small": 48}[tool.card_size])
        layout.addWidget(preview)

    @staticmethod
    def _text(text: str, name: str) -> QLabel:
        label = QLabel(text, objectName=name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _preview(self) -> QWidget:
        preview = QFrame(objectName="toolPreview")
        preview.setProperty("kind", self.tool.id)
        builders = {
            "watermark": self._watermark_preview,
            "resize": self._resize_preview,
            "background_remove": self._background_preview,
            "compression": self._compression_preview,
            "conversion": self._conversion_preview,
            "rename": self._rename_preview,
            "order_calendar": self._calendar_preview,
            "competitor_monitor": self._monitor_preview,
        }
        builders[self.tool.id](preview)
        return preview

    def _watermark_preview(self, preview: QFrame) -> None:
        layout = QHBoxLayout(preview)
        layout.setContentsMargins(9, 8, 10, 8)
        layout.setSpacing(10)
        thumbnail = QFrame(objectName="previewPhoto")
        thumb_layout = QVBoxLayout(thumbnail)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.addWidget(self._text("TEXT", "previewWatermark"))
        layout.addWidget(thumbnail, 1)
        values = QVBoxLayout()
        values.setSpacing(1)
        values.addWidget(QLabel("文字水印", objectName="previewCaption"))
        values.addWidget(QLabel("Opacity 50%", objectName="previewMetric"))
        layout.addLayout(values, 1)

    def _resize_preview(self, preview: QFrame) -> None:
        layout = QHBoxLayout(preview)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        layout.addWidget(self._text("1200 × 800", "previewDimension"), 1)
        layout.addWidget(self._text("↓", "previewArrow"))
        layout.addWidget(self._text("800 × 533", "previewDimension"), 1)

    def _background_preview(self, preview: QFrame) -> None:
        layout = QHBoxLayout(preview)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(8)
        before = QFrame(objectName="previewWhiteTile")
        before.setFixedSize(28, 28)
        layout.addWidget(before)
        layout.addWidget(self._text("→", "previewArrow"))
        checker = QWidget(objectName="previewChecker")
        checker.setFixedSize(28, 28)
        grid = QGridLayout(checker)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        for row in range(2):
            for column in range(2):
                cell = QFrame(objectName="previewCheckerLight" if (row + column) % 2 else "previewCheckerDark")
                grid.addWidget(cell, row, column)
        layout.addWidget(checker)
        layout.addWidget(QLabel("透明 PNG", objectName="previewCaption"))
        layout.addStretch()

    def _compression_preview(self, preview: QFrame) -> None:
        layout = QHBoxLayout(preview)
        layout.setContentsMargins(11, 8, 11, 8)
        layout.setSpacing(9)
        layout.addWidget(self._text("4.8 MB", "previewMetric"))
        track = QFrame(objectName="previewProgressTrack")
        track_layout = QHBoxLayout(track)
        track_layout.setContentsMargins(0, 0, 0, 0)
        fill = QFrame(objectName="previewProgressFill")
        fill.setFixedWidth(58)
        track_layout.addWidget(fill)
        track_layout.addStretch()
        layout.addWidget(track, 1)
        layout.addWidget(self._text("2.1 MB", "previewMetric"))

    def _conversion_preview(self, preview: QFrame) -> None:
        layout = QHBoxLayout(preview)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(7)
        layout.addWidget(self._text("JPG", "previewFormat"))
        layout.addWidget(self._text("→", "previewArrow"))
        layout.addWidget(self._text("PNG", "previewFormat"))
        layout.addStretch()

    def _rename_preview(self, preview: QFrame) -> None:
        layout = QHBoxLayout(preview)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(7)
        layout.addWidget(self._text("IMG_001", "previewFilename"), 1)
        layout.addWidget(self._text("↓", "previewArrow"))
        layout.addWidget(self._text("产品图_001", "previewFilename"), 1)

    def _calendar_preview(self, preview: QFrame) -> None:
        layout = QHBoxLayout(preview)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(7)
        date_tile = QFrame(objectName="previewDateTile")
        date_layout = QVBoxLayout(date_tile)
        date_layout.setContentsMargins(0, 1, 0, 1)
        date_layout.setSpacing(0)
        date_layout.addWidget(self._text("SEP", "previewDateMonth"))
        date_layout.addWidget(self._text("17", "previewDateDay"))
        layout.addWidget(date_tile)
        layout.addWidget(QLabel("待评价 3", objectName="previewBadge"))
        layout.addStretch()

    def _monitor_preview(self, preview: QFrame) -> None:
        layout = QHBoxLayout(preview)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        trend = QWidget(objectName="previewTrend")
        trend_layout = QHBoxLayout(trend)
        trend_layout.setContentsMargins(0, 0, 0, 0)
        trend_layout.setSpacing(3)
        for height in (7, 11, 9, 15):
            bar = QFrame(objectName="previewTrendBar")
            bar.setFixedSize(6, height)
            trend_layout.addWidget(bar, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(trend)
        layout.addWidget(self._text("¥45", "previewMetric"))
        layout.addWidget(self._text("→", "previewArrow"))
        layout.addWidget(self._text("¥50", "previewMetric"))
        layout.addStretch()


class DashboardPage(QWidget):
    _BENTO_POSITIONS = {
        "watermark": (0, 0, 2, 2),
        "resize": (0, 2, 1, 1),
        "background_remove": (1, 2, 1, 1),
        "compression": (2, 0, 1, 2),
        "conversion": (2, 2, 1, 1),
        "order_calendar": (3, 0, 1, 1),
        "rename": (3, 1, 1, 1),
        "competitor_monitor": (3, 2, 1, 1),
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
        layout.setContentsMargins(26, 20, 26, 12)
        layout.setSpacing(12)
        title_row = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(QLabel("所有工具", objectName="dashboardTitle"))
        titles.addWidget(QLabel("需要的工具，都在这里。", objectName="dashboardSubtitle"))
        title_row.addLayout(titles)
        title_row.addStretch()
        title_row.addWidget(QLabel(f"{len(TOOL_REGISTRY)} 个工具", objectName="toolCount"))
        layout.addLayout(title_row)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)
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
