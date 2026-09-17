from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget

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
        top = QRadialGradient(QPointF(rect.width() * 0.90, rect.height() * 0.08), rect.width() * 0.48)
        top.setColorAt(0, QColor(105, 161, 255, 46))
        top.setColorAt(1, QColor(247, 249, 253, 0))
        painter.fillRect(rect, QBrush(top))
        lower = QRadialGradient(QPointF(rect.width() * 0.08, rect.height() * 0.86), rect.width() * 0.58)
        lower.setColorAt(0, QColor(144, 126, 244, 34))
        lower.setColorAt(0.42, QColor(99, 171, 246, 28))
        lower.setColorAt(1, QColor(247, 249, 253, 0))
        painter.fillRect(rect, QBrush(lower))
        bottom = QLinearGradient(0, rect.height() * 0.65, 0, rect.height())
        bottom.setColorAt(0, QColor(247, 249, 253, 0))
        bottom.setColorAt(1, QColor(220, 235, 255, 48))
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
    def _box(p: QPainter, r: QRectF, color: str, radius: float = 7, border: str | None = None) -> None:
        p.setBrush(QColor(color))
        p.setPen(QPen(QColor(border), 1) if border else Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, radius, radius)

    def _text(self, p: QPainter, r: QRectF, text: str, color="#526175", px=9, bold=False, align=Qt.AlignmentFlag.AlignCenter) -> None:
        p.setPen(QColor(color))
        p.setFont(self._font(px, bold))
        p.drawText(r, int(align), text)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        outer = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        self._box(p, outer, "#F8FAFD", 12, "#EDF1F6")
        r = outer.adjusted(9, 8, -9, -8)
        getattr(self, f"_draw_{self.tool_id}")(p, r)

    def _draw_watermark(self, p, r):
        photo = QRectF(r.left(), r.top(), r.width() * .50, r.height())
        g = QLinearGradient(photo.topLeft(), photo.bottomRight())
        g.setColorAt(0, QColor("#CCE0FA")); g.setColorAt(1, QColor("#EEF4FB"))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(g)); p.drawRoundedRect(photo, 8, 8)
        p.save(); p.translate(photo.center()); p.rotate(-16); self._text(p, QRectF(-photo.width()/2, -10, photo.width(), 20), "SAMPLE WATERMARK", "#4168A6", 8, True); p.restore()
        info = QRectF(photo.right() + 10, r.top(), r.right() - photo.right() - 10, r.height())
        self._text(p, QRectF(info.left(), info.top(), info.width(), 18), "Opacity 40%", "#334155", 9, True, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        track = QRectF(info.left(), info.top()+27, info.width(), 5); self._box(p, track, "#DEE6F1", 2.5); self._box(p, QRectF(track.left(),track.top(),track.width()*.4,5), "#5A83E8", 2.5)
        self._text(p, QRectF(info.left(), info.bottom()-15, info.width(), 14), "示意预览", "#9AA6BA", 8, False, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def _draw_resize(self, p, r):
        w = (r.width()-30)/2
        a = QRectF(r.left(), r.top()+2, w, r.height()-4); b = QRectF(r.right()-w, r.top()+8, w, r.height()-16)
        for box, fill, label in ((a,"#ECF4FB","1200 × 800"),(b,"#E8F7F8","800 × 533")):
            self._box(p, box, fill, 8, "#DCE6EF"); self._box(p, box.adjusted(8,8,-8,-18), "#C9DCE9", 5); self._text(p, QRectF(box.left(),box.bottom()-17,box.width(),15), label, px=8, bold=True)
        self._text(p, QRectF(a.right(),r.top(),30,r.height()), "→", "#5F7FC0", 13, True)

    def _draw_background_remove(self, p, r):
        side = min(53, r.height()); a=QRectF(r.left()+4,r.center().y()-side/2,side,side); b=QRectF(r.right()-side-4,r.center().y()-side/2,side,side)
        self._box(p,a,"#FFFFFF",8,"#DCE3EC"); self._box(p,QRectF(a.center().x()-12,a.center().y()-17,24,34),"#B9CCE2",7)
        cell=side/4
        for row in range(4):
            for col in range(4):
                p.fillRect(QRectF(b.left()+col*cell,b.top()+row*cell,cell+.4,cell+.4), QColor("#FFFFFF") if (row+col)%2 else QColor("#DDE5EE"))
        self._box(p,QRectF(b.center().x()-12,b.center().y()-17,24,34),"#9D8AE1",7); self._text(p,QRectF(a.right(),r.top(),r.width()-side*2-8,r.height()),"→","#6F69C4",14,True)

    def _draw_compression(self, p, r):
        thumb=QRectF(r.left(),r.top(),55,r.height()); self._box(p,thumb,"#E5E0F7",8)
        info=QRectF(thumb.right()+10,r.top(),r.width()-thumb.width()-10,r.height())
        self._text(p,QRectF(info.left(),info.top(),info.width(),17),"2.4 MB  →  420 KB","#334155",9,True,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self._text(p,QRectF(info.right()-42,info.top(),42,17),"-83%","#6950C8",9,True,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        track=QRectF(info.left(),info.center().y()+2,info.width(),6); self._box(p,track,"#E2E6F0",3); self._box(p,QRectF(track.left(),track.top(),track.width()*.83,6),"#866CE0",3)
        self._text(p,QRectF(info.left(),info.bottom()-14,info.width(),13),"示意 UI","#9AA6BA",8,False,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

    def _draw_conversion(self, p, r):
        w=min(75,(r.width()-34)/2); a=QRectF(r.left()+8,r.top()+5,w,r.height()-10); b=QRectF(r.right()-w-8,r.top()+5,w,r.height()-10)
        self._box(p,a,"#EEF1FF",8,"#DFE4F8"); self._box(p,b,"#EDEBFF",8,"#E0DCF7"); self._text(p,a,"JPG","#5366C4",11,True); self._text(p,b,"PNG","#6C5BC3",11,True); self._text(p,QRectF(a.right(),r.top(),b.left()-a.right(),r.height()),"→","#7381B5",13,True)

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
        self._text(p,QRectF(r.left(),r.top(),40,16),"¥45","#334155",9,True,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter); self._text(p,QRectF(r.right()-40,r.top(),40,16),"¥50","#334155",9,True,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        chart=QRectF(r.left()+2,r.top()+22,r.width()-4,r.height()-24); pts=[QPointF(chart.left(),chart.bottom()-8),QPointF(chart.left()+chart.width()*.23,chart.bottom()-19),QPointF(chart.left()+chart.width()*.47,chart.bottom()-16),QPointF(chart.left()+chart.width()*.70,chart.top()+12),QPointF(chart.right(),chart.top()+7)]; path=QPainterPath(pts[0])
        for point in pts[1:]: path.lineTo(point)
        p.setPen(QPen(QColor("#21A276"),2)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(path); p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor("#21A276")); p.drawEllipse(pts[-1],3,3)
        badge=QRectF(r.right()-55,r.top()+16,55,19); self._box(p,badge,"#E7F7F0",7); self._text(p,badge,"+11.1%","#168761",8,True)


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
        layout=QVBoxLayout(self); layout.setContentsMargins(16,15,16,15); layout.setSpacing(7)
        header=QHBoxLayout(); header.setSpacing(9); header.addWidget(IconTile(tool)); meta=QVBoxLayout(); meta.setSpacing(1); meta.addWidget(QLabel(tool.category,objectName="toolCardCategory"))
        if tool.featured: meta.addWidget(QLabel("Popular",objectName="featuredBadge"),0,Qt.AlignmentFlag.AlignLeft)
        header.addLayout(meta); header.addStretch(); header.addWidget(QLabel("↗",objectName="toolCardArrow"),0,Qt.AlignmentFlag.AlignTop); layout.addLayout(header)
        layout.addWidget(QLabel(tool.name,objectName="toolCardTitle")); description=QLabel(tool.description,objectName="toolCardDescription"); description.setWordWrap(True); description.setMaximumHeight(32); layout.addWidget(description); layout.addStretch(1); layout.addWidget(ToolPreview(tool.id))
