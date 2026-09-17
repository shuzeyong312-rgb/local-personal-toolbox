from app.tool_registry import TOOL_REGISTRY, dock_tools, tools_in_category


def test_tool_registry_is_the_complete_navigation_source():
    assert [tool.id for tool in TOOL_REGISTRY] == [
        "watermark", "resize", "background_remove", "compression", "conversion", "rename", "order_calendar", "competitor_monitor",
    ]
    assert {tool.id for tool in dock_tools()} == {"watermark", "resize", "compression", "order_calendar", "competitor_monitor"}
    assert {tool.name for tool in tools_in_category("图片工具")} == {"批量打水印", "修改图片尺寸", "白底转透明", "批量图片压缩", "图片格式转换"}
