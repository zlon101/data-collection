# debug_utils.py
import logging
from pathlib import Path
from poco.drivers.android.uiautomation import AndroidUiautomationPoco

from common.file_manager import write_json_path

logger = logging.getLogger(__name__)


def dump_ui_tree(
    poco: AndroidUiautomationPoco,
    output_path: str = "outputs/ui_tree.json",
) -> dict:
    """
    将当前屏幕的完整 UI 控件树导出为 JSON 文件，用于离线分析节点结构。

    使用场景：
      - 不知道目标节点的 resource-id / text 时，先 dump 整棵树
      - 开发时保存树结构，后续脚本直接对照树写选择器

    Returns:
        UI 树的字典表示。
    """
    # dump() 返回当前屏幕完整的控件树（嵌套字典结构）
    hierarchy: dict = poco.agent.hierarchy.dump()

    out = Path(output_path)
    write_json_path(hierarchy, out)

    logger.info("UI 树已导出: %s", out.resolve())
    return hierarchy


def find_all_texts(hierarchy: dict, result: list | None = None) -> list[str]:
    """
    递归遍历 UI 树，提取所有非空 text 属性（快速定位文本节点位置）。

    Args:
        hierarchy: dump_ui_tree 的返回值。
        result: 递归用内部参数，外部调用无需传入。

    Returns:
        页面上所有可见文本的列表。
    """
    if result is None:
        result = []

    text = hierarchy.get("payload", {}).get("text", "")
    if text and text.strip():
        result.append(text.strip())

    for child in hierarchy.get("children", []):
        find_all_texts(child, result)

    return result


def print_node_info(node) -> None:
    """
    打印单个 Poco 节点的所有可用属性，用于确认节点内容。

    Args:
        node: 通过 poco(...) 查询到的节点对象。
    """
    attrs_to_check = [
        "text", "name", "type", "enabled", "visible",
        "clickable", "content-desc", "resource-id",
        "checked", "selected", "focusable",
    ]
    logger.info("── 节点属性详情 ──")
    for attr in attrs_to_check:
        try:
            val = node.attr(attr)
            if val is not None and val != "":
                logger.info("  %-20s = %s", attr, val)
        except Exception:
            pass

    try:
        bounds = node.get_bounds()
        logger.info("  %-20s = %s", "bounds", bounds)
    except Exception:
        pass