from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QButtonGroup, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.tool_registry import TOOL_REGISTRY, ToolDefinition
from app.widgets.dashboard import FilterChip, ToolCard


class DashboardPage(QWidget):
    """Personal Toolbox home page.

    Dashboard visuals are isolated in app.widgets.dashboard. Business tool pages
    and factories remain untouched.
    """

    def __init__(self, open_tool: Callable[[str], None]) -> None:
        super().__init__(objectName="dashboardPage")
        self._open_tool = open_tool
        self._query = ""
        self._sort_key = "popular"
        self._columns = 3
        self._settings = QSettings("Personal Toolbox", "Personal Toolbox")
        self.cards = {tool.id: ToolCard(tool) for tool in TOOL_REGISTRY}
        for tool_id, card in self.cards.items():
            card.clicked.connect(lambda _checked=False, current=tool_id: self._launch(current))
        self._build_ui()
        self._refresh_grid()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(objectName="dashboardScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget(objectName="dashboardContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 18, 32, 112)
        layout.setSpacing(16)

        heading = QHBoxLayout()
        heading.setSpacing(18)
        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(QLabel("所有工具", objectName="dashboardTitle"))
        titles.addWidget(QLabel("需要的工具，都在这里。", objectName="dashboardSubtitle"))
        heading.addLayout(titles)
        heading.addStretch(1)

        controls = QVBoxLayout()
        controls.setSpacing(6)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(7)
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        for label, key in (("Popular", "popular"), ("A → Z", "alpha"), ("最近使用", "recent")):
            chip = FilterChip(label, key)
            chip.setChecked(key == self._sort_key)
            chip.clicked.connect(lambda _checked=False, current=key: self._set_sort(current))
            self.filter_group.addButton(chip)
            filter_row.addWidget(chip)
        controls.addLayout(filter_row)
        self.tool_count = QLabel(objectName="toolCount")
        self.tool_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        controls.addWidget(self.tool_count)
        heading.addLayout(controls)
        layout.addLayout(heading)

        self.grid_host = QWidget(objectName="dashboardGridHost")
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        layout.addWidget(self.grid_host)

        self.empty = QLabel("没有找到匹配的工具", objectName="dashboardEmpty")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.hide()
        layout.addWidget(self.empty)
        layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)
        self._scroll = scroll

    def filter_tools(self, query: str) -> None:
        self._query = query.strip().casefold()
        self._refresh_grid()

    def _launch(self, tool_id: str) -> None:
        self._remember_recent(tool_id)
        self._open_tool(tool_id)

    def _set_sort(self, key: str) -> None:
        if key == self._sort_key:
            return
        self._sort_key = key
        self._refresh_grid()

    def _recent_ids(self) -> list[str]:
        value = self._settings.value("dashboard/recent_tools", [])
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, (tuple, list)):
            return [str(item) for item in value if str(item)]
        return []

    def _remember_recent(self, tool_id: str) -> None:
        ids = [item for item in self._recent_ids() if item != tool_id]
        ids.insert(0, tool_id)
        self._settings.setValue("dashboard/recent_tools", ids[:8])
        if self._sort_key == "recent":
            self._refresh_grid()

    def _ordered_tools(self) -> list[ToolDefinition]:
        tools = list(TOOL_REGISTRY)
        if self._sort_key == "alpha":
            tools.sort(key=lambda item: item.name.casefold())
        elif self._sort_key == "recent":
            recents = self._recent_ids()
            rank = {tool_id: index for index, tool_id in enumerate(recents)}
            tools.sort(key=lambda item: (rank.get(item.id, len(rank) + 1), TOOL_REGISTRY.index(item)))
        else:
            tools.sort(key=lambda item: (not item.featured, TOOL_REGISTRY.index(item)))
        if self._query:
            tools = [tool for tool in tools if self._query in " ".join((tool.name, tool.description, tool.category)).casefold()]
        return tools

    def _clear_grid(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()

    def _refresh_grid(self) -> None:
        self._clear_grid()
        tools = self._ordered_tools()
        for index, tool in enumerate(tools):
            card = self.cards[tool.id]
            card.show()
            self.grid.addWidget(card, index // self._columns, index % self._columns)
        for column in range(3):
            self.grid.setColumnStretch(column, 1 if column < self._columns else 0)
        self.tool_count.setText(f"{len(tools)} / {len(TOOL_REGISTRY)} 个工具")
        self.empty.setVisible(not tools)
        self.grid_host.setVisible(bool(tools))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        available = self._scroll.viewport().width() if hasattr(self, "_scroll") else self.width()
        columns = 3 if available >= 900 else 2
        if columns != self._columns:
            self._columns = columns
            self._refresh_grid()
