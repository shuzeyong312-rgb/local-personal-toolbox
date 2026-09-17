from __future__ import annotations

import json
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QHeaderView, QMenu, QTableWidgetItem, QToolButton

from tools.competitor_monitor.page import (
    CompetitorMonitorPage as BaseCompetitorMonitorPage,
    ProductCell,
)


MISSING_FIELD_LABELS = {
    "title": "商品标题",
    "price_raw_values": "价格",
    "min_order_qty": "起批量",
    "sales_raw": "页面已售",
    "visible_sku_names": "SKU",
    "listed_at": "上架时间",
    "month_sales_raw": "月成交",
    "month_distribution_raw": "月铺货",
    "year_sales_quantity_raw": "年销量",
    "year_sales_orders_raw": "年订单量",
}

STATUS_STYLES = {
    "success": "color:#176B45;background:#EAF7F0;border:1px solid #C9ECDD;",
    "warning": "color:#9A5B13;background:#FFF7E8;border:1px solid #F2D39A;",
    "danger": "color:#B42318;background:#FEF0F0;border:1px solid #F4C7C3;",
    "paused": "color:#667085;background:#F2F4F7;border:1px solid #DDE1E6;",
    "pending": "color:#52667E;background:#F4F7FA;border:1px solid #D8E1EB;",
}


@dataclass(frozen=True)
class CompetitorRowView:
    competitor_id: int
    title: str
    shop_name: str
    meta: str
    price: str
    sales: str
    month_sales: str
    sku_count: str
    latest_change: str
    status_text: str
    status_tone: str
    status_tooltip: str


class StatusBadge(QLabel):
    def __init__(self, text: str, tone: str, tooltip: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(72)
        self.setMaximumHeight(26)
        self.setToolTip(tooltip)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        style = STATUS_STYLES.get(tone, STATUS_STYLES["pending"])
        self.setStyleSheet(
            f"QLabel {{{style} border-radius:10px; padding:3px 8px; font-size:12px; font-weight:700;}}"
        )


def build_row_view(row, snapshot) -> CompetitorRowView:
    title = row["title"] or row["alias"] or row["offer_id"]
    shop_name = row["shop_name"] or "店铺未知"
    group_name = row["group_name"] or "未分组"
    alias = (row["alias"] or "").strip()
    meta = group_name if not alias or alias == title else f"{group_name} · {alias}"

    missing_fields = _json_list(snapshot, "missing_fields_json")
    status_text, status_tone, status_tooltip = _display_status(row, snapshot, missing_fields)

    sku_names = _json_list(snapshot, "visible_sku_names_json")
    sku_count = str(len(sku_names)) if snapshot and sku_names else "--"

    return CompetitorRowView(
        competitor_id=row["id"],
        title=title,
        shop_name=shop_name,
        meta=meta,
        price=_compact_price(snapshot),
        sales=_snapshot_text(snapshot, "sales_raw"),
        month_sales=_snapshot_text(snapshot, "month_sales_raw"),
        sku_count=sku_count,
        latest_change=row["latest_change"] or "--",
        status_text=status_text,
        status_tone=status_tone,
        status_tooltip=status_tooltip,
    )


def _display_status(row, snapshot, missing_fields: list[str]) -> tuple[str, str, str]:
    if not bool(row["monitor_enabled"]) or row["status"] == "暂停":
        return "已暂停", "paused", "该商品已暂停自动监控。"

    if row["status"] == "最近采集失败":
        return "采集失败", "danger", "最近一次采集失败；已有历史快照不会被覆盖。"

    if snapshot is None or row["status"] == "待验证":
        return "待采集", "pending", "尚未获得可用快照，请执行一次采集。"

    if row["status"] == "部分异常" or snapshot["collection_status"] == "partial":
        labels = [MISSING_FIELD_LABELS.get(name, name) for name in missing_fields]
        detail = "、".join(labels) or "部分辅助字段"
        return "数据缺失", "warning", f"本次页面读取成功，但暂未获取：{detail}。不等同于采集失败。"

    return "正常", "success", "最近一次采集成功，关键监控数据可用。"


def _compact_price(snapshot) -> str:
    if not snapshot:
        return "--"
    minimum = snapshot["display_price_min"]
    maximum = snapshot["display_price_max"]
    if minimum is None:
        return "--"
    low = _number_text(minimum)
    high = _number_text(maximum if maximum is not None else minimum)
    return f"¥{low}" if low == high else f"¥{low}–{high}"


def _number_text(value) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:g}"


def _snapshot_text(snapshot, field: str) -> str:
    if not snapshot or snapshot[field] in (None, ""):
        return "--"
    return str(snapshot[field])


def _json_list(row, field: str) -> list:
    if not row or not row[field]:
        return []
    try:
        value = json.loads(row[field])
    except (TypeError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def _item(text: str, competitor_id: int, *, tooltip: str | None = None, centered: bool = False) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setData(Qt.ItemDataRole.UserRole, competitor_id)
    item.setToolTip(tooltip if tooltip is not None else text)
    if centered:
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    return item


class CompetitorMonitorPage(BaseCompetitorMonitorPage):
    """Competitor monitor page with a single-layer, business-oriented product table.

    The legacy page owns collection, history and settings behavior. This presentation layer
    deliberately owns only the product-list view model and rendering so cell widgets and
    QTableWidgetItems never render competing text in the same cell.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.only_failed.setText("仅看需关注")
        self.only_failed.setToolTip("显示数据缺失或最近采集失败的商品")
        self._configure_product_table()
        for label in self.findChildren(QLabel):
            if label.text() == "采集异常":
                label.setText("需关注")
        self.refresh()

    def _configure_product_table(self) -> None:
        self.table.setHorizontalHeaderLabels(("商品信息", "价格", "页面已售", "月成交", "SKU", "最近变化", "监控状态", "操作"))
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 8):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
        for column, width in enumerate((0, 100, 90, 86, 58, 124, 96, 54)):
            if column:
                self.table.setColumnWidth(column, width)

    def refresh(self) -> None:
        rows = self.store.competitors(self.group_filter.currentData())
        needle = self.product_search.text().strip().casefold()
        if needle:
            rows = [
                row for row in rows
                if needle in " ".join((
                    row["title"] or "", row["alias"] or "", row["offer_id"],
                    row["shop_name"] or "", row["group_name"] or "",
                )).casefold()
            ]
        if self.only_changed.isChecked():
            rows = [row for row in rows if row["latest_change"]]
        if self.only_failed.isChecked():
            rows = [row for row in rows if row["status"] in ("部分异常", "最近采集失败")]

        # clearContents removes stale cell widgets as well as items. Each visible cell below
        # gets exactly one text layer; widget-backed cells keep only a blank metadata item.
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            snapshot = self.store.latest_snapshot(row["id"])
            view = build_row_view(row, snapshot)

            identity = _item("", view.competitor_id, tooltip=view.title)
            self.table.setItem(row_index, 0, identity)
            product = ProductCell(view.title, view.shop_name, view.meta)
            product.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.table.setCellWidget(row_index, 0, product)

            values = (view.price, view.sales, view.month_sales, view.sku_count, view.latest_change)
            for column, value in enumerate(values, 1):
                self.table.setItem(row_index, column, _item(value, view.competitor_id, centered=True))

            status_item = _item("", view.competitor_id, tooltip=view.status_tooltip)
            self.table.setItem(row_index, 6, status_item)
            self.table.setCellWidget(
                row_index, 6,
                StatusBadge(view.status_text, view.status_tone, view.status_tooltip),
            )

            action_item = _item("", view.competitor_id)
            self.table.setItem(row_index, 7, action_item)
            action = QToolButton(objectName="rowMenu")
            action.setText("···")
            action.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            menu = QMenu(action)
            actions = (
                ("立即采集", self.collect_selected),
                ("查看详情", self.open_history),
                ("编辑", self.edit_selected),
                ("恢复监控" if row["status"] == "暂停" else "暂停监控", self.toggle_selected),
                ("删除", self.delete_selected),
            )
            for label, slot in actions:
                menu.addAction(
                    label,
                    lambda checked=False, rid=view.competitor_id, fn=slot: self._run_row_action(rid, fn),
                )
            action.setMenu(menu)
            self.table.setCellWidget(row_index, 7, action)
            self.table.setRowHeight(row_index, 76)

        self.show_latest()
        self.refresh_dashboard()
        self.refresh_events()
