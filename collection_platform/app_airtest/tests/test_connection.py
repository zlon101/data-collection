# tests/test_connection.py
"""
设备连接与 Poco 初始化的冒烟测试。

运行方式（在项目根目录执行）：
    uv run python tests/test_connection.py

测试通过的判断标准：
  1. ADB 能找到并连接设备（USB 已插入且已开启 USB 调试）。
  2. Poco 能成功与设备上的 UIAutomation 服务握手。
  3. 能成功 dump 出 UI 树（至少包含根节点）。
  4. 截图能保存到 outputs/ 目录。
"""

import logging
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，确保在任意位置运行均可找到模块
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.devices import (
    ADB_PATH,
    USB_DEVICE_SERIAL,
    POCO_DEFAULT_TIMEOUT,
)
from core import setup_android_device, create_android_poco
from debug_utils import dump_ui_tree, find_all_texts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("test_connection")

OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_device_connection() -> bool:
    """
    冒烟测试 1：验证 ADB 设备连接。

    Returns:
        True 表示通过，False 表示失败。
    """
    logger.info("═══ [1/4] 测试 ADB 设备连接 ═══")
    try:
        setup_android_device(
            mode="usb",
            device_serial=USB_DEVICE_SERIAL,
            adb_path=ADB_PATH,
        )
        logger.info("✓ 设备连接成功")
        return True
    except ConnectionError as exc:
        logger.error("✗ 设备连接失败: %s", exc)
        logger.error("  → 请检查：1) USB 线已插稳  2) 手机已开启「USB 调试」  "
                     "3) 电脑已被手机信任（弹窗授权）")
        return False


def test_poco_init() -> object | None:
    """
    冒烟测试 2：验证 Poco 初始化（UIAutomation 服务握手）。

    Returns:
        成功时返回 Poco 实例，失败时返回 None。
    """
    logger.info("═══ [2/4] 测试 Poco 初始化 ═══")
    try:
        poco = create_android_poco(timeout=POCO_DEFAULT_TIMEOUT)
        logger.info("✓ Poco 初始化成功")
        return poco
    except RuntimeError as exc:
        logger.error("✗ Poco 初始化失败: %s", exc)
        logger.error("  → 常见原因：pocoservice.apk 未安装或版本不匹配，"
                     "尝试重新插拔 USB 后重跑")
        return None


def test_ui_dump(poco) -> bool:
    """
    冒烟测试 3：验证 UI 树 dump 功能。

    Args:
        poco: 已初始化的 Poco 实例。

    Returns:
        True 表示通过，False 表示失败。
    """
    logger.info("═══ [3/4] 测试 UI 树 dump ═══")
    try:
        tree = dump_ui_tree(
            poco,
            output_path=str(OUTPUT_DIR / "test_ui_tree.json"),
        )
        texts = find_all_texts(tree)
        logger.info("✓ UI 树 dump 成功，页面文本数量: %d", len(texts))
        if texts:
            logger.info("  当前页面前 5 条文本: %s", texts[:5])
        return True
    except Exception as exc:
        logger.error("✗ UI 树 dump 失败: %s", exc)
        return False


def test_screenshot() -> bool:
    """
    冒烟测试 4：验证 Airtest 截图功能。

    Returns:
        True 表示通过，False 表示失败。
    """
    logger.info("═══ [4/4] 测试截图功能 ═══")
    try:
        from airtest.core.api import snapshot
        snap_path = str(OUTPUT_DIR / "test_snapshot.jpg")
        snapshot(filename=snap_path)
        if Path(snap_path).exists():
            logger.info("✓ 截图成功，已保存: %s", snap_path)
            return True
        else:
            logger.error("✗ 截图文件未生成")
            return False
    except Exception as exc:
        logger.error("✗ 截图失败: %s", exc)
        return False


def main() -> None:
    """运行全部冒烟测试，输出通过/失败汇总。"""
    results: dict[str, bool] = {}

    # 1. 设备连接（失败则后续无法进行）
    results["设备连接"] = test_device_connection()
    if not results["设备连接"]:
        logger.error("设备连接失败，终止后续测试。")
        _print_summary(results)
        sys.exit(1)

    # 2. Poco 初始化
    poco = test_poco_init()
    results["Poco 初始化"] = poco is not None
    if poco is None:
        logger.error("Poco 初始化失败，跳过 UI dump 测试。")
        results["UI Dump"] = False
    else:
        # 3. UI dump
        results["UI Dump"] = test_ui_dump(poco)

    # 4. 截图
    results["截图"] = test_screenshot()

    _print_summary(results)
    failed = [k for k, v in results.items() if not v]
    sys.exit(1 if failed else 0)


def _print_summary(results: dict[str, bool]) -> None:
    """打印测试汇总表格。"""
    logger.info("")
    logger.info("══════════ 测试汇总 ══════════")
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info("  %-15s %s", name, status)
    total = len(results)
    passed_count = sum(results.values())
    logger.info("  ─────────────────────────")
    logger.info("  结果: %d / %d 通过", passed_count, total)
    logger.info("══════════════════════════════")


if __name__ == "__main__":
    main()
