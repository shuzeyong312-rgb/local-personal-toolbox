from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from app.icons import icon
from app.tool_registry import ToolDefinition


TOOL_ACCENTS = {
    "watermark": ("#3568F4", "#EAF0FF"),
    "resize": ("#1A9CB0", "#E7F7FA"),
    "background_remove": ("#7667E8", "#F0EDFF"),
    "compression": ("#8057E8", "#F2ECFF"),
    "conversion": ("#5D69E8", "#EDF0FF"),
    "rename": ("#8A5AD8", "#F4EDFC"),
    "order_calendar": ("#159B7B", "#E7F8F2"),
    "competitor_monitor": ("#149269", "#E8F7F0"),
}


class AmbientBackground(QWidget):
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        painter.fillRect(rect, QColor("#F7F9FD"))

        top = QRadialGradient(QPointF(rect.width() * 0.88, rect.height() * 0.04), rect.width() * 0.62)
        top.setColorAt(0, QColor(102, 158, 255, 62))
        top.setColorAt(0.48, QColor(174, 207, 255, 30))
        top.setColorAt(1, QColor(247, 249, 253, 0))
        painter.fillRect(rect, QBrush(top))

        lower_blue = QRadialGradient(QPointF(rect.width() * 0.02, rect.height() * 0.92), rect.width() * 0.72)
        lower_blue.setColorAt(0, QColor(105, 174, 255, 46))
        lower_blue.setColorAt(0.55, QColor(200, 225, 255, 22))
        lower_blue.setColorAt(1, QColor(247, 249, 253, 0))
        painter.fillRect(rect, QBrush(lower_blue))

        lower_violet = QRadialGradient(QPointF(rect.width() * 0.14, rect.height() * 1.02), rect.width() * 0.52)
        lower_violet.setColorAt(0, QColor(166, 135, 245, 43))
        lower_violet.setColorAt(0.58, QColor(216, 204, 252, 19))
        lower_violet.setColorAt(1, QColor(247, 249, 253, 0))
        painter.fillRect(rect, QBrush(lower_violet))

        bottom = QLinearGradient(0, rect.height() * 0.64, 0, rect.height())
        bottom.setColorAt(0, QColor(247, 249, 253, 0))
        bottom.setColorAt(1, QColor(210, 231, 255, 52))
        painter.fillRect(rect, QBrush(bottom))


class BrandMark(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(42, 42)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0.5, 0.5, 41, 41)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor("#3479F6"))
        g.setColorAt(1, QColor("#3157D9"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, 12, 12)
        p.setBrush(QColor(255, 255, 255, 240))
        for x, y in ((15, 15), (27, 15), (15, 27), (27, 27)):
            p.drawEllipse(QPointF(x, y), 3, 3)


class IconTile(QFrame):
    def __init__(self, tool: ToolDefinition) -> None:
        super().__init__(objectName="dashboardIconTile")
        accent, soft = TOOL_ACCENTS[tool.id]
        self.setFixedSize(42, 42)
        self.setStyleSheet(f"background:{soft}; border:1px solid rgba(255,255,255,190); border-radius:12px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setPixmap(icon(tool.icon, accent, 20).pixmap(20, 20))
        layout.addWidget(label)


class FilterChip(QPushButton):
    def __init__(self, text: str, key: str) -> None:
        super().__init__(text, objectName="filterChip")
        self.key = key
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class ToolPreview(QWidget):
    def __init__(self, tool_id: str) -> None:
        super().__init__(objectName="toolPreviewCanvas")
        self.tool_id = tool_id
        self.setFixedHeight(78)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    @staticmethod
    def _font(px: int, bold: bool = False) -> QFont:
        font = QFont("Segoe UI Variable")
        font.setPixelSize(px)
        font.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
        return font

    @staticmethod
    def _box(p: QPainter, r: QRectF, color: str | QColor, radius: float = 7, border: str | QColor | None = None) -> None:
        p.setBrush(QColor(color) if isinstance(color, str) else color)
        p.setPen(QPen(QColor(border) if isinstance(border, str) else border, 1) if border else Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, radius, radius)

    def _text(self, p: QPainter, r: QRectF, text: str, color="#526175", px=9, bold=False, align=Qt.AlignmentFlag.AlignCenter) -> None:
        p.setPen(QColor(color))
        p.setFont(self._font(px, bold))
        p.drawText(r, int(align), text)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        outer = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        self._box(p, outer, QColor(255, 255, 255, 146), 12, QColor(226, 234, 245, 170))
        r = outer.adjusted(9, 8, -9, -8)
        getattr(self, f"_draw_{self.tool_id}")(p, r)

    def _draw_watermark(self, p, r):
        photo = QRectF(r.left(), r.top(), r.width() * .48, r.height())
        g = QLinearGradient(photo.topLeft(), photo.bottomRight())
        g.setColorAt(0, QColor("#CFE5F8"))
        g.setColorAt(.56, QColor("#E9F2F4"))
        g.setColorAt(1, QColor("#D8E7D8"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawRoundedRect(photo, 8, 8)
        p.setBrush(QColor(255, 255, 255, 215))
        p.drawRoundedRect(QRectF(photo.center().x() - 11, photo.top() + 14, 22, 31), 6, 6)
        p.setBrush(QColor("#90A6BB"))
        p.drawRoundedRect(QRectF(photo.center().x() - 5, photo.top() + 9, 10, 9), 3, 3)
        p.save()
        p.translate(photo.center())
        p.rotate(-17)
        self._text(p, QRectF(-photo.width() / 2, -8, photo.width(), 16), "SAMPLE WATERMARK", QColor(46, 83, 143, 155), 7, True)
        p.restore()

        info = QRectF(photo.right() + 10, r.top(), r.right() - photo.right() - 10, r.height())
        self._text(p, QRectF(info.left(), info.top(), info.width(), 16), "Opacity 40%", "#334155", 9, True, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        track = QRectF(info.left(), info.top() + 25, info.width(), 4)
        self._box(p, track, "#DFE7F2", 2)
        self._box(p, QRectF(track.left(), track.top(), track.width() * .4, 4), "#6289E8", 2)
        p.setBrush(QColor("#FFFFFF"))
        p.setPen(QPen(QColor("#6289E8"), 1.5))
        p.drawEllipse(QPointF(track.left() + track.width() * .4, track.center().y()), 4, 4)
        badge = QRectF(info.left(), info.bottom() - 17, min(38, info.width()), 16)
        self._box(p, badge, "#EEF3FB", 5)
        self._text(p, badge, "文字", "#6E7E94", 7, True)
        self._text(p, QRectF(badge.right() + 4, badge.top(), info.right() - badge.right() - 4, 16), "-17°", "#8794A8", 8, True)

    def _draw_resize(self, p, r):
        w = (r.width()-30)/2
        a = QRectF(r.left(), r.top()+2, w, r.height()-4); b = QRectF(r.right()-w, r.top()+8, w, r.height()-16)
        for box, fill, label in ((a,"#ECF4FB","1200 × 800"),(b,"#E8F7F8","800 × 533")):
            self._box(p, box, fill, 8, "#DCE6EF"); self._box(p, box.adjusted(8,8,-8,-18), "#C9DCE9", 5); self._text(p, QRectF(box.left(),box.bottom()-17,box.width(),15), label, px=8, bold=True)
        self._text(p, QRectF(a.right(),r.top(),30,r.height()), "→", "#5F7FC0", 13, True)

    def _draw_background_remove(self, p, r):
        side = min(53, r.height())
        a = QRectF(r.left() + 4, r.center().y() - side / 2, side, side)
        b = QRectF(r.right() - side - 4, r.center().y() - side / 2, side, side)
        self._box(p, a, "#FFFFFF", 8, "#DDE5EE")

        def product(box, body, cap):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(cap))
            p.drawRoundedRect(QRectF(box.center().x() - 6, box.top() + 8, 12, 8), 3, 3)
            p.setBrush(QColor(body))
            p.drawRoundedRect(QRectF(box.center().x() - 13, box.top() + 14, 26, 31), 8, 8)
            p.setBrush(QColor(255, 255, 255, 145))
            p.drawRoundedRect(QRectF(box.center().x() - 7, box.top() + 23, 14, 8), 3, 3)

        product(a, "#CAD7E6", "#91A5BC")
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(b, 8, 8)
        p.setClipPath(clip)
        cell = side / 6
        for row in range(6):
            for col in range(6):
                p.fillRect(QRectF(b.left() + col * cell, b.top() + row * cell, cell + .4, cell + .4), QColor("#FFFFFF") if (row + col) % 2 else QColor("#DCE4ED"))
        p.restore()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor("#D8E1EC"), 1))
        p.drawRoundedRect(b, 8, 8)
        product(b, "#9989DC", "#6F61BD")
        self._text(p, QRectF(a.right(), r.top(), r.width() - side * 2 - 8, r.height()), "→", "#7772C8", 14, True)

    def _draw_compression(self, p, r):
        thumb=QRectF(r.left(),r.top(),55,r.height()); self._box(p,thumb,"#E5E0F7",8)
        info=QRectF(thumb.right()+10,r.top(),r.width()-thumb.width()-10,r.height())
        self._text(p,QRectF(info.left(),info.top(),info.width(),17),"2.4 MB  →  420 KB","#334155",9,True,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self._text(p,QRectF(info.right()-42,info.top(),42,17),"-83%","#6950C8",9,True,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        track=QRectF(info.left(),info.center().y()+2,info.width(),6); self._box(p,track,"#E2E6F0",3); self._box(p,QRectF(track.left(),track.top(),track.width()*.83,6),"#866CE0",3)
        self._text(p,QRectF(info.left(),info.bottom()-14,info.width(),13),"示意 UI","#9AA6BA",8,False,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

    def _draw_conversion(self, p, r):
        w = min(82, (r.width() - 34) / 2)
        a = QRectF(r.left() + 4, r.top() + 2, w, r.height() - 4)
        b = QRectF(r.right() - w - 4, r.top() + 2, w, r.height() - 4)

        def file_card(box, fmt, filename, fill, accent):
            self._box(p, box, fill, 8, "#DEE5F2")
            badge = QRectF(box.left() + 7, box.top() + 7, 31, 18)
            self._box(p, badge, accent, 5)
            self._text(p, badge, fmt, "#FFFFFF", 8, True)
            p.setPen(QPen(QColor("#CBD5E4"), 1))
            p.drawLine(QPointF(box.left() + 8, box.top() + 32), QPointF(box.right() - 8, box.top() + 32))
            self._text(p, QRectF(box.left() + 7, box.bottom() - 22, box.width() - 14, 16), filename, "#64748B", 7, False, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        file_card(a, "JPG", "IMG_001.jpg", "#F7F9FF", "#6677D8")
        file_card(b, "PNG", "IMG_001.png", "#F6F4FF", "#8069D2")
        self._text(p, QRectF(a.right(), r.top(), b.left() - a.right(), r.height()), "→", "#7381B5", 13, True)

    def _draw_rename(self, p, r):
        for i,(a,b) in enumerate((("IMG_001.jpg","产品图_001.jpg"),("IMG_002.jpg","产品图_002.jpg"))):
            y=r.top()+i*29; left=QRectF(r.left(),y,r.width()*.40,23); right=QRectF(r.right()-r.width()*.43,y,r.width()*.43,23)
            self._box(p,left,"#FFFFFF",6,"#E3E8EF"); self._box(p,right,"#F5EFFB",6,"#E8DDF4")
            self._text(p,left.adjusted(6,0,-6,0),a,"#71809C",8,False,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter); self._text(p,right.adjusted(6,0,-6,0),b,"#76519F",8,True,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter); self._text(p,QRectF(left.right(),y,right.left()-left.right(),23),"→","#8C76A7",10,True)

    def _draw_order_calendar(self, p, r):
        cal=QRectF(r.left(),r.top(),r.width()*.68,r.height()); days=("09","10","11","16","17","18"); gap=4; cw=(cal.width()-gap*2)/3; ch=(cal.height()-gap)/2
        for i,day in enumerate(days):
            row,col=divmod(i,3); box=QRectF(cal.left()+col*(cw+gap),cal.top()+row*(ch+gap),cw,ch); active=day=="17"; self._box(p,box,"#E8F7F2" if active else "#FFFFFF",6,"#DDEAE6"); self._text(p,box,day,"#13866A" if active else "#71809C",8,active)
        badge=QRectF(cal.right()+9,r.center().y()-14,r.right()-cal.right()-9,28); self._box(p,badge,"#EAF8F2",8); self._text(p,badge,"3 待评价","#247B62",8,True)

    def _draw_competitor_monitor(self, p, r):
        self._text(p, QRectF(r.left(), r.top(), 40, 16), "¥45", "#334155", 9, True, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._text(p, QRectF(r.right() - 40, r.top(), 40, 16), "¥50", "#334155", 9, True, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        badge = QRectF(r.center().x() - 26, r.top() - 1, 52, 18)
        self._box(p, badge, "#E7F7F0", 7)
        self._text(p, badge, "+11.1%", "#168761", 8, True)

        chart = QRectF(r.left() + 2, r.top() + 23, r.width() - 4, r.height() - 25)
        p.setPen(QPen(QColor(175, 195, 208, 75), 1, Qt.PenStyle.DashLine))
        for ratio in (.25, .7):
            y = chart.top() + chart.height() * ratio
            p.drawLine(QPointF(chart.left(), y), QPointF(chart.right(), y))
        points = [
            QPointF(chart.left(), chart.bottom() - 7),
            QPointF(chart.left() + chart.width() * .23, chart.bottom() - 18),
            QPointF(chart.left() + chart.width() * .47, chart.bottom() - 15),
            QPointF(chart.left() + chart.width() * .70, chart.top() + 12),
            QPointF(chart.right(), chart.top() + 6),
        ]
        line = QPainterPath(points[0])
        for point in points[1:]:
            line.lineTo(point)
        area = QPainterPath(line)
        area.lineTo(chart.right(), chart.bottom())
        area.lineTo(chart.left(), chart.bottom())
        area.closeSubpath()
        fade = QLinearGradient(0, chart.top(), 0, chart.bottom())
        fade.setColorAt(0, QColor(33, 162, 118, 45))
        fade.setColorAt(1, QColor(33, 162, 118, 2))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(fade))
        p.drawPath(area)
        p.setPen(QPen(QColor("#21A276"), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(line)
        p.setPen(QPen(QColor("#FFFFFF"), 1.5))
        p.setBrush(QColor("#21A276"))
        p.drawEllipse(points[-1], 3.5, 3.5)


class ToolCard(QToolButton):
    def __init__(self, tool: ToolDefinition) -> None:
        super().__init__(objectName="toolCard")
        self.tool = tool
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(220)
        self.setFixedHeight(210)
        self.setToolTip(f"打开{tool.name}")
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(24)
        self._shadow.setOffset(0, 6)
        self._shadow.setColor(QColor(46, 67, 101, 22))
        self.setGraphicsEffect(self._shadow)
        layout=QVBoxLayout(self); layout.setContentsMargins(16,15,16,15); layout.setSpacing(7)
        header=QHBoxLayout(); header.setSpacing(9); header.addWidget(IconTile(tool)); meta=QVBoxLayout(); meta.setSpacing(1); meta.addWidget(QLabel(tool.category,objectName="toolCardCategory"))
        if tool.featured: meta.addWidget(QLabel("Popular",objectName="featuredBadge"),0,Qt.AlignmentFlag.AlignLeft)
        header.addLayout(meta); header.addStretch(); header.addWidget(QLabel("↗",objectName="toolCardArrow"),0,Qt.AlignmentFlag.AlignTop); layout.addLayout(header)
        layout.addWidget(QLabel(tool.name,objectName="toolCardTitle")); description=QLabel(tool.description,objectName="toolCardDescription"); description.setWordWrap(True); description.setMaximumHeight(32); layout.addWidget(description); layout.addStretch(1); layout.addWidget(ToolPreview(tool.id))

    def enterEvent(self, event) -> None:
        self._shadow.setBlurRadius(29)
        self._shadow.setColor(QColor(46, 67, 101, 34))
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._shadow.setBlurRadius(24)
        self._shadow.setColor(QColor(46, 67, 101, 22))
        super().leaveEvent(event)
