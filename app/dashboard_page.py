from __future__ import annotations

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.dashboard_theme import DASHBOARD_STYLE
from app.icons import dashboard_icon
from app.tool_registry import TOOL_SPECS, ToolSpec
from app.widgets.dashboard import FloatingDock, ToolCard


class DashboardPage(QWidget):
    toolActivated = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, objectName="dashboardPage")
        self.setStyleSheet(DASHBOARD_STYLE)
        self.settings = QSettings("PersonalToolbox", "LocalPersonalToolbox")
        self.sort_mode = "popular"
        self._columns = 0
        self._cards = {spec.page_index: ToolCard(spec) for spec in TOOL_SPECS}
        for card in self._cards.values():
            card.activated.connect(self._activate_tool)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll = QScrollArea(objectName="dashboardScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.canvas = QWidget(objectName="dashboardCanvas")
        self.scroll.setWidget(self.canvas)
        root.addWidget(self.scroll)

        content = QVBoxLayout(self.canvas)
        content.setContentsMargins(34, 18, 34, 106)
        content.setSpacing(0)

        content.addLayout(self._search_row())
        content.addSpacing(24)
        content.addLayout(self._title_row())
        content.addSpacing(4)
        self.count_label = QLabel(objectName="toolCount")
        content.addWidget(self.count_label)
        content.addSpacing(18)

        self.grid_host = QWidget(objectName="dashboardContent")
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(16)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        content.addWidget(self.grid_host)
        content.addStretch(1)

        self.empty_label = QLabel("没有匹配的工具，换一个关键词试试。", objectName="emptySearch", parent=self.grid_host)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()

        self.dock = FloatingDock(self)
        self.dock.toolActivated.connect(self._activate_tool)
        self.dock.homeActivated.connect(lambda: self.scroll.verticalScrollBar().setValue(0))
        self.dock.raise_()

        shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        shortcut.activated.connect(self._focus_search)
        self._shortcut = shortcut

        self._rebuild_grid(force=True)

    def _search_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        surface = QWidget(objectName="searchSurface")
        surface.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        surface.setMaximumWidth(720)
        surface.setMinimumWidth(430)
        surface.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        inner = QHBoxLayout(surface)
        inner.setContentsMargins(16, 2, 12, 2)
        inner.setSpacing(9)

        search_icon = QLabel()
        search_icon.setFixedSize(22, 22)
        search_icon.setPixmap(dashboard_icon("search", "#8290A7", 18).pixmap(18, 18))
        inner.addWidget(search_icon)
        self.search = QLineEdit(objectName="dashboardSearch")
        self.search.setPlaceholderText("搜索工具、输入关键词或命令...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _text: self._rebuild_grid())
        inner.addWidget(self.search, 1)
        inner.addWidget(QLabel("Ctrl K", objectName="shortcutBadge"))

        row.addWidget(surface, 1)
        row.addStretch(1)
        return row

    def _title_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(18)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(QLabel("所有工具", objectName="dashboardTitle"))
        title_box.addWidget(QLabel("需要的工具，都在这里。", objectName="dashboardSubtitle"))
        row.addLayout(title_box, 1)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        for text, mode in (("Popular", "popular"), ("A → Z", "az"), ("最近使用", "recent")):
            button = QPushButton(text, objectName="filterChip")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, selected=mode: self._set_sort(selected))
            self.filter_group.addButton(button)
            row.addWidget(button, 0, Qt.AlignmentFlag.AlignBottom)
            if mode == "popular":
                button.setChecked(True)
        return row

    def _focus_search(self) -> None:
        self.search.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search.selectAll()

    def _set_sort(self, mode: str) -> None:
        self.sort_mode = mode
        self._rebuild_grid()

    def _recent_pages(self) -> list[int]:
        value = self.settings.value("dashboard/recent_tools", [])
        if value is None:
            return []
        if not isinstance(value, (list, tuple)):
            value = [value]
        recent: list[int] = []
        for item in value:
            try:
                page = int(item)
            except (TypeError, ValueError):
                continue
            if page not in recent:
                recent.append(page)
        return recent

    def record_recent(self, page_index: int) -> None:
        recent = [page for page in self._recent_pages() if page != page_index]
        recent.insert(0, page_index)
        self.settings.setValue("dashboard/recent_tools", recent[:8])
        if self.sort_mode == "recent":
            self._rebuild_grid()

    def _activate_tool(self, page_index: int) -> None:
        self.record_recent(page_index)
        self.toolActivated.emit(page_index)

    def _visible_specs(self) -> list[ToolSpec]:
        query = self.search.text().strip().lower()
        specs = list(TOOL_SPECS)
        if query:
            specs = [
                spec
                for spec in specs
                if query in " ".join((spec.name, spec.category, spec.description, *spec.keywords)).lower()
            ]
        if self.sort_mode == "az":
            specs.sort(key=lambda spec: spec.name.casefold())
        elif self.sort_mode == "recent":
            recent = self._recent_pages()
            position = {page: idx for idx, page in enumerate(recent)}
            specs.sort(key=lambda spec: (position.get(spec.page_index, 999), spec.featured_rank))
        else:
            specs.sort(key=lambda spec: spec.featured_rank)
        return specs

    def _desired_columns(self) -> int:
        width = max(1, self.scroll.viewport().width())
        if width >= 900:
            return 3
        if width >= 620:
            return 2
        return 1

    def _rebuild_grid(self, force: bool = False) -> None:
        specs = self._visible_specs()
        columns = self._desired_columns()
        if not force and columns == self._columns and getattr(self, "_last_pages", None) == [s.page_index for s in specs]:
            self.count_label.setText(f"{len(specs)} 个工具")
            return
        self._columns = columns
        self._last_pages = [s.page_index for s in specs]

        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()

        self.empty_label.hide()
        if not specs:
            self.grid.addWidget(self.empty_label, 0, 0, 1, max(1, columns))
            self.empty_label.show()
        else:
            for index, spec in enumerate(specs):
                row, col = divmod(index, columns)
                card = self._cards[spec.page_index]
                self.grid.addWidget(card, row, col)
                card.show()
            for col in range(columns):
                self.grid.setColumnStretch(col, 1)
        self.count_label.setText(f"{len(specs)} 个工具")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rebuild_grid()
        if hasattr(self, "dock"):
            dock_x = max(12, (self.width() - self.dock.width()) // 2)
            dock_y = max(12, self.height() - self.dock.height() - 20)
            self.dock.move(dock_x, dock_y)
            self.dock.raise_()
