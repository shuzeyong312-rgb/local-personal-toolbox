from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from tools.background_remove.page import BackgroundRemovePage
from tools.compression.page import CompressionPage
from tools.competitor_monitor.product_view import CompetitorMonitorPage
from tools.conversion.page import ConversionPage
from tools.order_calendar.page import OrderCalendarPage
from tools.rename.page import RenamePage
from tools.resize.page import ResizePage
from tools.watermark.page import WatermarkPage


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    name: str
    description: str
    category: str
    icon: str
    page_factory: Callable[[], QWidget]
    featured: bool = False
    dock: bool = False
    card_size: str = "medium"


TOOL_REGISTRY = (
    ToolDefinition("watermark", "批量打水印", "为多张图片添加统一文字水印，原图不会被覆盖。", "图片工具", "stamp", WatermarkPage, True, True, "large"),
    ToolDefinition("resize", "修改图片尺寸", "统一尺寸或按比例缩放图片。", "图片工具", "image", ResizePage, False, True),
    ToolDefinition("background_remove", "白底转透明", "批量移除浅色商品背景，生成透明 PNG。", "图片工具", "cutout", BackgroundRemovePage),
    ToolDefinition("compression", "批量图片压缩", "减小文件体积，尽量保持图片清晰。", "图片工具", "compress", CompressionPage, False, True, "small"),
    ToolDefinition("conversion", "图片格式转换", "在 JPG、PNG、WebP 与 BMP 间批量转换。", "图片工具", "convert", ConversionPage, False, False, "small"),
    ToolDefinition("rename", "批量重命名", "预览后安全地统一文件名称。", "文件工具", "rename", RenamePage, False, False, "small"),
    ToolDefinition("order_calendar", "出单日历", "安排出单节奏并跟踪待评价记录。", "电商运营", "calendar", OrderCalendarPage, False, True),
    ToolDefinition("competitor_monitor", "1688竞品监控", "跟踪竞品价格、销量和异常变化。", "电商运营", "monitor", CompetitorMonitorPage, False, True, "large"),
)


TOOLS_BY_ID = {tool.id: tool for tool in TOOL_REGISTRY}


def tools_in_category(category: str) -> tuple[ToolDefinition, ...]:
    return tuple(tool for tool in TOOL_REGISTRY if tool.category == category)


def dock_tools() -> tuple[ToolDefinition, ...]:
    return tuple(tool for tool in TOOL_REGISTRY if tool.dock)
