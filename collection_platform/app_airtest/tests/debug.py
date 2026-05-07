# tests/debug.py
"""
调试示例脚本：演示如何使用 debug_utils 在纯代码环境中探查 UI 结构。

前提：已通过 USB 连接设备并完成 ADB 授权。

运行方式（从项目根目录执行）：
    uv run --directory collection_platform/app_airtest python3 tests/debug.py
"""

import sys
from pathlib import Path

from scrapers._path_utils import get_project_root

APP_AIRTEST_ROOT = get_project_root() / "collection_platform" / "app_airtest"

from config.devices import ADB_PATH, USB_DEVICE_SERIAL, POCO_DEFAULT_TIMEOUT
from core import setup_android_device, create_android_poco
from debug_utils import dump_ui_tree, find_all_texts, print_node_info


def main() -> None:
    # ── Step 1: 连接设备 ──────────────────────────────────────
    setup_android_device(
        mode="usb",
        device_serial=USB_DEVICE_SERIAL,
        adb_path=ADB_PATH,
    )

    # ── Step 2: 初始化 Poco ───────────────────────────────────
    poco = create_android_poco(timeout=POCO_DEFAULT_TIMEOUT)

    # ── Step 3: dump 当前屏幕的完整 UI 控件树 ─────────────────
    # 输出到 outputs/ui_tree_home.json，用文本编辑器打开后
    # 搜索 resource-id 或 text 即可定位目标节点的选择器写法。
    tree = dump_ui_tree(poco, "outputs/ui_tree_home.json")

    # ── Step 4: 快速列出页面上的所有文本（判断页面是否正确加载）
    texts = find_all_texts(tree)
    print("\n当前页面可见文本：")
    for t in texts:
        print(f"  · {t}")

    # ── Step 5: 定位特定节点并打印其完整属性 ─────────────────
    # 示例：查找文本为"阅读"的节点（替换为实际页面上存在的文本）
    target_text = "阅读"
    target = poco(text=target_text)

    try:
        # exists() 不抛异常，先判断节点是否存在再打印属性
        if target.exists():
            print(f"\n节点「{target_text}」的属性：")
            print_node_info(target)
        else:
            print(f"\n当前页面未找到文本为「{target_text}」的节点，"
                  "请修改 target_text 为页面上实际存在的文本后重试。")
    except Exception as exc:
        print(f"节点查询异常: {exc}")


if __name__ == "__main__":
    main()
