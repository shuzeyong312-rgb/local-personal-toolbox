from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


PATHS = {
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/>',
    "stamp": '<path d="M5 22h14"/><path d="M19 17H5v-2a3 3 0 0 1 3-3h1V7a3 3 0 0 1 6 0v5h1a3 3 0 0 1 3 3v2Z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "folder": '<path d="M3 6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
    "folder-open": '<path d="M3 7V6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v2"/><path d="M3 10h18l-2 9H5Z"/>',
    "rename": '<path d="M4 7V4h16v3M9 20h6M12 4v16"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>',
    "monitor": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-7"/>',
    "resize": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 12V8h4M16 12v4h-4M12 8 8 12M12 16l4-4"/>',
    "transparent": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M4 10h16M10 4v16M4 16h16M16 4v16"/>',
    "compress": '<path d="M8 3v5H3M16 3v5h5M8 21v-5H3M16 21v-5h5"/><path d="m3 8 5-5M21 8l-5-5M3 16l5 5M21 16l-5 5"/>',
    "convert": '<path d="M7 7h11l-3-3M18 7l-3 3"/><path d="M17 17H6l3 3M6 17l3-3"/>',
    "home": '<path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10M9 20v-6h6v6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "shield": '<path d="M12 3 5 6v5c0 5 3 8 7 10 4-2 7-5 7-10V6Z"/><path d="m9 12 2 2 4-4"/>',
    "minimize": '<path d="M5 12h14"/>',
    "maximize": '<rect x="5" y="5" width="14" height="14" rx="1"/>',
    "restore": '<path d="M8 8V5h11v11h-3"/><rect x="5" y="8" width="11" height="11" rx="1"/>',
    "close": '<path d="m6 6 12 12M18 6 6 18"/>',
}


def _svg_icon(name: str, color: str, size: int, stroke_width: float) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}</svg>'''
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(QSize(size * 2, size * 2))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


def icon(name: str, color: str = "#64748B", size: int = 18) -> QIcon:
    return _svg_icon(name, color, size, 2)


def dashboard_icon(name: str, color: str = "#64748B", size: int = 18) -> QIcon:
    """Slightly heavier local SVG icon used by Dashboard surfaces only."""
    return _svg_icon(name, color, size, 1.8)
