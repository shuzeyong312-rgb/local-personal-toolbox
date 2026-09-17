from __future__ import annotations

from math import ceil

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.icons import dashboard_icon
from app.tool_registry import TOOL_SPECS, ToolSpec


class AmbientBackground(QWidget):
    """Lightweight painted ambient background shared by sidebar and content."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, objectName="ambientRoot")
        self.setAutoFillBackground(False)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#F7F9FD"))
        w, h = max(1, self.width()), max(1, self.height())

        top_right = QRadialGradient(QPointF(w * 0.90, h * 0.07), w * 0.48)
        top_right.setColorAt(0.0, QColor(91, 150, 255, 35))
        top_right.setColorAt(0.55, QColor(118, 170, 255, 15))
        top_right.setColorAt(1.0, QColor(247, 249, 253, 0))
        painter.fillRect(self.rect(), top_right)

        lower_left = QRadialGradient(QPointF(w * 0.06, h * 0.92), w * 0.58)
        lower_left.setColorAt(0.0, QColor(133, 112, 241, 27))
        lower_left.setColorAt(0.35, QColor(87, 169, 244, 20))
        lower_left.setColorAt(1.0, QColor(247, 249, 253, 0))
        painter.fillRect(self.rect(), lower_left)

        bottom = QLinearGradient(0, h * 0.72, 0, h)
        bottom.setColorAt(0.0, QColor(247, 249, 253, 0))
        bottom.setColorAt(1.0, QColor(216, 233, 255, 26))
        painter.fillRect(self.rect(), bottom)
        painter.end()
        super().paintEvent(event)


class BrandMark(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(42, 42)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.5, 0.5, 41, 41)
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor("#4A8CFF"))
        grad.setColorAt(1.0, QColor("#2763E8"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawRoundedRect(rect, 12, 12)
        painter.setBrush(QColor(255, 255, 255, 235))
        for x in (15, 25):
            for y in (15, 25):
                painter.drawEllipse(QPointF(x, y), 2.5, 2.5)
        painter.end()


class IconBadge(QWidget):
    def __init__(self, icon_name: str, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.icon_name = icon_name
        self.accent = QColor(accent)
        self.setFixedSize(42, 42)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.5, 0.5, 41, 41)
        bg = QColor(self.accent)
        bg.setAlpha(24)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 12, 12)
        dashboard_icon(self.icon_name, self.accent.name(), 20).paint(painter, 11, 11, 20, 20)
        painter.end()


class ToolPreview(QWidget):
    def __init__(self, kind: str, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.kind = kind
        self.accent = QColor(accent)
        self.setMinimumHeight(78)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _rounded(self, painter: QPainter, rect: QRectF, fill: QColor | str, radius: float = 9,
                 border: QColor | str | None = None) -> None:
        painter.setPen(QPen(QColor(border), 1) if border else Qt.PenStyle.NoPen)
        painter.setBrush(QColor(fill))
        painter.drawRoundedRect(rect, radius, radius)

    @staticmethod
    def _font(painter: QPainter, size: int, weight: int = 500) -> None:
        font = QFont("Segoe UI Variable", size)
        font.setWeight(QFont.Weight(weight))
        painter.setFont(font)

    def _text(self, painter: QPainter, rect: QRectF, text: str, color: str = "#65738B",
              size: int = 9, weight: int = 500, align=Qt.AlignmentFlag.AlignCenter) -> None:
        self._font(painter, size, weight)
        painter.setPen(QColor(color))
        painter.drawText(rect, align, text)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0.5, 0.5, max(1, self.width() - 1), max(1, self.height() - 1))
        self._rounded(painter, r, QColor(247, 249, 253, 190), 12, QColor(224, 231, 242, 140))
        method = getattr(self, f"_paint_{self.kind}", self._paint_default)
        method(painter, r.adjusted(10, 9, -10, -9))
        painter.end()

    def _paint_default(self, painter: QPainter, r: QRectF) -> None:
        self._text(painter, r, "Preview", "#8C98AB", 10, 600)

    def _paint_watermark(self, painter: QPainter, r: QRectF) -> None:
        image = QRectF(r.left(), r.top(), r.width() * 0.63, r.height())
        grad = QLinearGradient(image.topLeft(), image.bottomRight())
        grad.setColorAt(0.0, QColor("#D9E8F9"))
        grad.setColorAt(1.0, QColor("#EEF3F8"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawRoundedRect(image, 8, 8)
        painter.save()
        painter.translate(image.center())
        painter.rotate(-15)
        painter.setPen(QColor(39, 82, 140, 105))
        self._font(painter, 7, 650)
        painter.drawText(QRectF(-image.width() * .42, -8, image.width() * .84, 16), Qt.AlignmentFlag.AlignCenter,
                         "SAMPLE WATERMARK")
        painter.restore()
        right = QRectF(image.right() + 8, r.top(), r.right() - image.right() - 8, r.height())
        self._text(painter, QRectF(right.left(), right.top(), right.width(), 18), "Opacity", "#8793A6", 8, 600)
        self._text(painter, QRectF(right.left(), right.top() + 17, right.width(), 18), "40%", "#334155", 11, 700)
        y = right.bottom() - 10
        pen = QPen(QColor("#D7DFEA")); pen.setWidthF(3); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QPointF(right.left() + 3, y), QPointF(right.right() - 3, y))
        pen = QPen(self.accent); pen.setWidthF(3); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QPointF(right.left() + 3, y), QPointF(right.left() + right.width() * .42, y))
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(QPen(self.accent, 2))
        painter.drawEllipse(QPointF(right.left() + right.width() * .42, y), 4, 4)

    def _paint_resize(self, painter: QPainter, r: QRectF) -> None:
        gap = 24
        w = (r.width() - gap) / 2
        left = QRectF(r.left(), r.top() + 5, w, r.height() - 10)
        right = QRectF(left.right() + gap, left.top() + 6, w, left.height() - 12)
        for rect, text, fill in ((left, "1200 × 800", "#E9F2FA"), (right, "800 × 533", "#E8F6F7")):
            self._rounded(painter, rect, fill, 8)
            self._text(painter, QRectF(rect.left(), rect.bottom() - 21, rect.width(), 18), text, "#5D6C82", 8, 650)
            painter.setPen(QPen(QColor("#B8C7D9"), 1))
            painter.drawLine(QPointF(rect.left() + 8, rect.top() + 12), QPointF(rect.right() - 8, rect.top() + 12))
        self._text(painter, QRectF(left.right(), r.top(), gap, r.height()), "→", "#8B99AD", 13, 650)

    def _paint_transparent(self, painter: QPainter, r: QRectF) -> None:
        gap = 22
        w = (r.width() - gap) / 2
        left = QRectF(r.left(), r.top(), w, r.height())
        right = QRectF(left.right() + gap, r.top(), w, r.height())
        self._rounded(painter, left, "#FFFFFF", 8, "#E4EAF2")
        cell = 8
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(right, 8, 8)
        painter.setClipPath(path)
        rows = ceil(right.height() / cell)
        cols = ceil(right.width() / cell)
        for y in range(rows):
            for x in range(cols):
                painter.fillRect(QRectF(right.left() + x * cell, right.top() + y * cell, cell, cell),
                                 QColor("#EEF1F5") if (x + y) % 2 else QColor("#FFFFFF"))
        painter.restore()
        for rect in (left, right):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#6F88A6"))
            painter.drawRoundedRect(QRectF(rect.center().x() - 10, rect.center().y() - 14, 20, 28), 7, 7)
            painter.setBrush(QColor("#A9C8DD"))
            painter.drawEllipse(QPointF(rect.center().x(), rect.center().y() - 6), 5, 5)
        self._text(painter, QRectF(left.right(), r.top(), gap, r.height()), "→", "#8B99AD", 13, 650)

    def _paint_compression(self, painter: QPainter, r: QRectF) -> None:
        gap = 22
        w = (r.width() - gap) / 2
        left = QRectF(r.left(), r.top() + 2, w, r.height() - 4)
        right = QRectF(left.right() + gap, left.top(), w, left.height())
        for rect, size, fill in ((left, "2.4 MB", "#E8EEF8"), (right, "420 KB", "#EEEAFB")):
            self._rounded(painter, rect, fill, 8)
            self._text(painter, QRectF(rect.left(), rect.bottom() - 23, rect.width(), 18), size, "#475569", 9, 700)
        self._text(painter, QRectF(left.right(), r.top(), gap, r.height()), "→", "#8B99AD", 13, 650)
        badge = QRectF(right.right() - 41, right.top() + 5, 35, 16)
        self._rounded(painter, badge, QColor(92, 73, 196, 28), 8)
        self._text(painter, badge, "-83%", "#7568DF", 7, 700)

    def _paint_conversion(self, painter: QPainter, r: QRectF) -> None:
        card_w = min(84, r.width() * .34)
        left = QRectF(r.left() + 3, r.top() + 4, card_w, r.height() - 8)
        right = QRectF(r.right() - card_w - 3, r.top() + 4, card_w, r.height() - 8)
        self._rounded(painter, left, "#ECF2FB", 8)
        self._rounded(painter, right, "#EEEFFD", 8)
        self._text(painter, left, "JPG", "#4D6686", 11, 700)
        self._text(painter, right, "PNG", "#5A5CB4", 11, 700)
        self._text(painter, QRectF(left.right(), r.top(), right.left() - left.right(), r.height()), "→", "#8794A8", 14, 700)

    def _paint_rename(self, painter: QPainter, r: QRectF) -> None:
        left_w = r.width() * .42
        arrow_w = r.width() * .12
        left = QRectF(r.left(), r.top(), left_w, r.height())
        right = QRectF(left.right() + arrow_w, r.top(), r.width() - left_w - arrow_w, r.height())
        for i, text in enumerate(("IMG_001.jpg", "IMG_002.jpg")):
            row = QRectF(left.left(), left.top() + i * 27, left.width(), 22)
            self._rounded(painter, row, "#F1F4F8", 6)
            self._text(painter, row.adjusted(6, 0, -4, 0), text, "#6C788A", 7, 600, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        for i, text in enumerate(("产品图_001.jpg", "产品图_002.jpg")):
            row = QRectF(right.left(), right.top() + i * 27, right.width(), 22)
            self._rounded(painter, row, "#F1EEFB", 6)
            self._text(painter, row.adjusted(6, 0, -4, 0), text, "#675C91", 7, 600, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self._text(painter, QRectF(left.right(), r.top(), arrow_w, r.height()), "→", "#8B99AD", 12, 650)

    def _paint_calendar(self, painter: QPainter, r: QRectF) -> None:
        cal = QRectF(r.left(), r.top(), r.width() * .68, r.height())
        dates = (("09", "10", "11"), ("16", "17", "18"))
        cell_w = cal.width() / 3
        cell_h = cal.height() / 2
        for row, values in enumerate(dates):
            for col, value in enumerate(values):
                cell = QRectF(cal.left() + col * cell_w + 2, cal.top() + row * cell_h + 2, cell_w - 4, cell_h - 4)
                if value == "17":
                    self._rounded(painter, cell, QColor(39, 168, 122, 30), 7)
                    self._text(painter, cell, value, "#238963", 9, 700)
                else:
                    self._text(painter, cell, value, "#77869A", 8, 600)
        info = QRectF(cal.right() + 8, r.top(), r.right() - cal.right() - 8, r.height())
        self._text(painter, QRectF(info.left(), info.top() + 8, info.width(), 20), "3", "#238963", 13, 700)
        self._text(painter, QRectF(info.left(), info.top() + 30, info.width(), 18), "待评价", "#7F8C9F", 8, 600)

    def _paint_monitor(self, painter: QPainter, r: QRectF) -> None:
        chart = QRectF(r.left() + 2, r.top() + 8, r.width() * .58, r.height() - 16)
        points = [0.72, 0.64, 0.69, 0.48, 0.54, 0.30, 0.20]
        pen = QPen(self.accent)
        pen.setWidthF(2.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        last = None
        for i, value in enumerate(points):
            p = QPointF(chart.left() + i * chart.width() / (len(points) - 1), chart.top() + value * chart.height())
            if last is not None:
                painter.drawLine(last, p)
            last = p
        info = QRectF(chart.right() + 12, r.top(), r.right() - chart.right() - 12, r.height())
        self._text(painter, QRectF(info.left(), info.top(), info.width(), 18), "¥45 → ¥50", "#455468", 9, 700)
        self._text(painter, QRectF(info.left(), info.top() + 22, info.width(), 18), "+11.1%", "#239C68", 10, 700)


class ToolCard(QFrame):
    activated = Signal(int)

    def __init__(self, spec: ToolSpec, parent: QWidget | None = None) -> None:
        super().__init__(parent, objectName="toolCard")
        self.spec = spec
        self.setProperty("hovered", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(184)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 14, 15, 13)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(IconBadge(spec.icon_name, spec.accent))
        titles = QVBoxLayout()
        titles.setSpacing(1)
        titles.addWidget(QLabel(spec.category, objectName="toolCardCategory"))
        titles.addWidget(QLabel(spec.name, objectName="toolCardTitle"))
        header.addLayout(titles, 1)
        arrow = QLabel("↗")
        arrow.setStyleSheet("color:#A4AFBF; font-size:14px; background:transparent;")
        header.addWidget(arrow, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        description = QLabel(spec.description, objectName="toolCardDescription")
        description.setWordWrap(False)
        description.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(description)
        layout.addWidget(ToolPreview(spec.preview_kind, spec.accent), 1)

    def enterEvent(self, event) -> None:
        self.setProperty("hovered", True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.setProperty("hovered", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.activated.emit(self.spec.page_index)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class FloatingDock(QWidget):
    toolActivated = Signal(int)
    homeActivated = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, objectName="dockSurface")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(11, 10, 11, 10)
        layout.setSpacing(7)

        home = QPushButton(objectName="dockHome")
        home.setIcon(dashboard_icon("home", "#FFFFFF", 20))
        home.setToolTip("首页")
        home.clicked.connect(self.homeActivated)
        layout.addWidget(home)

        for spec in TOOL_SPECS:
            button = QPushButton(objectName="dockItem")
            button.setIcon(dashboard_icon(spec.icon_name, spec.accent, 19))
            button.setToolTip(spec.name)
            button.clicked.connect(lambda _checked=False, index=spec.page_index: self.toolActivated.emit(index))
            layout.addWidget(button)

        self.setFixedHeight(66)
        self.setFixedWidth(11 * 2 + 9 * 44 + 8 * 7)
