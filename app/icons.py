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
    "home": '<path d="m3 11 9-8 9 8v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z"/><path d="M9 21v-6h6v6"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    "sun": '<circle cx="12" cy="12" r="3.5"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "arrow-left": '<path d="m15 18-6-6 6-6"/><path d="M9 12h12"/>',
    "cutout": '<path d="M4 4h16v16H4z"/><path d="M9 4v16M4 9h16"/><circle cx="14" cy="14" r="3"/>',
    "compress": '<path d="M7 4H4v3M17 4h3v3M7 20H4v-3M17 20h3v-3"/><path d="M8 12h8M12 8l4 4-4 4"/>',
    "convert": '<path d="M7 7h11l-3-3M17 17H6l3 3"/>',
    "minimize": '<path d="M5 12h14"/>',
    "maximize": '<rect x="5" y="5" width="14" height="14" rx="1"/>',
    "restore": '<path d="M8 8V5h11v11h-3"/><rect x="5" y="8" width="11" height="11" rx="1"/>',
    "close": '<path d="m6 6 12 12M18 6 6 18"/>',
}


def icon(name: str, color: str = "#64748B", size: int = 18) -> QIcon:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}</svg>'''
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(QSize(size * 2, size * 2))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)
