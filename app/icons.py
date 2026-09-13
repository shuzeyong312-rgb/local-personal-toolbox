from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


PATHS = {
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/>',
    "stamp": '<path d="M5 22h14"/><path d="M19 17H5v-2a3 3 0 0 1 3-3h1V7a3 3 0 0 1 6 0v5h1a3 3 0 0 1 3 3v2Z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "folder": '<path d="M3 6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
    "folder-open": '<path d="M3 7V6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v2"/><path d="M3 10h18l-2 9H5Z"/>',
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
