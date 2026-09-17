from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolSpec:
    key: str
    name: str
    category: str
    description: str
    icon_name: str
    accent: str
    preview_kind: str
    page_index: int
    featured_rank: int
    keywords: tuple[str, ...] = ()


TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        "watermark",
        "批量打水印",
        "图片工具",
        "批量添加文字水印，保留原图尺寸与质量策略。",
        "stamp",
        "#3478F6",
        "watermark",
        0,
        0,
        ("水印", "批量", "图片", "watermark"),
    ),
    ToolSpec(
        "resize",
        "修改图片尺寸",
        "图片工具",
        "按目标尺寸批量缩放图片，快速统一商品素材规格。",
        "resize",
        "#2E9DCA",
        "resize",
        1,
        1,
        ("尺寸", "缩放", "分辨率", "resize"),
    ),
    ToolSpec(
        "background_remove",
        "白底转透明",
        "图片工具",
        "将纯白或近白背景转换为透明背景。",
        "transparent",
        "#7568DF",
        "transparent",
        2,
        2,
        ("白底", "透明", "抠图", "background"),
    ),
    ToolSpec(
        "compression",
        "批量图片压缩",
        "图片工具",
        "批量减小图片体积，适合电商上传与素材归档。",
        "compress",
        "#8A5CF6",
        "compression",
        3,
        3,
        ("压缩", "体积", "图片", "compression"),
    ),
    ToolSpec(
        "conversion",
        "图片格式转换",
        "图片工具",
        "JPG、PNG、WebP、BMP 等常用格式批量转换。",
        "convert",
        "#5B6FF5",
        "conversion",
        4,
        4,
        ("格式", "转换", "jpg", "png", "webp", "bmp"),
    ),
    ToolSpec(
        "rename",
        "批量重命名",
        "文件工具",
        "按规则批量整理文件名，减少重复手工操作。",
        "rename",
        "#7C61D9",
        "rename",
        5,
        5,
        ("文件名", "重命名", "排序", "rename"),
    ),
    ToolSpec(
        "order_calendar",
        "出单日历",
        "电商运营",
        "按日期查看出单任务、阶段进度与待评价事项。",
        "calendar",
        "#27A87A",
        "calendar",
        6,
        6,
        ("订单", "日历", "评价", "运营"),
    ),
    ToolSpec(
        "competitor_monitor",
        "1688竞品监控",
        "电商运营",
        "记录竞品价格与销量快照，观察异常变化。",
        "monitor",
        "#239C68",
        "monitor",
        7,
        7,
        ("1688", "竞品", "价格", "销量", "监控"),
    ),
)

TOOL_BY_KEY = {tool.key: tool for tool in TOOL_SPECS}
TOOL_BY_PAGE = {tool.page_index: tool for tool in TOOL_SPECS}

CATEGORY_ORDER = ("图片工具", "文件工具", "电商运营")


def tools_for_category(category: str) -> tuple[ToolSpec, ...]:
    return tuple(tool for tool in TOOL_SPECS if tool.category == category)
