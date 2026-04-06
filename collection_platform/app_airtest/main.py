# main.py
"""
项目主入口。

用法：
  uv run python main.py                      # 自动启动 App 并抓取（默认）
  uv run python main.py --mode manual        # 手动打开 App，按 Enter 后抓取
  uv run python main.py --test               # 设备连接冒烟测试
  uv run python main.py --dump               # dump 当前屏幕 UI 树（调试用）

所有业务配置统一从 config/devices.py 读取。
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.devices import (
    ADB_PATH,
    APP_PACKAGE,
    APP_COLD_START_WAIT,
    POCO_DEFAULT_TIMEOUT,
    USB_DEVICE_SERIAL,
)
from core import setup_android_device, create_android_poco

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("main")


def run_scraper(launch_mode: Literal["auto", "manual"]) -> None:
    """数据抓取流程，透传 launch_mode 给 scraper。"""
    from scrapers.app_scraper import main as scraper_main
    scraper_main(launch_mode=launch_mode)


def run_connection_test() -> None:
    """设备连接冒烟测试。"""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tests" / "test_connection.py")],
        check=False,
    )
    sys.exit(result.returncode)


def run_dump() -> None:
    """连接设备并 dump 当前 UI 树到 outputs/ui_tree_dump.json。"""
    from debug_utils import dump_ui_tree, find_all_texts

    setup_android_device(
        mode="usb",
        device_serial=USB_DEVICE_SERIAL,
        adb_path=ADB_PATH,
    )
    poco = create_android_poco(timeout=POCO_DEFAULT_TIMEOUT)

    output_path = str(PROJECT_ROOT / "outputs" / "ui_tree_dump.json")
    tree = dump_ui_tree(poco, output_path)
    texts = find_all_texts(tree)

    logger.info("UI 树已导出: %s", output_path)
    logger.info("页面文本列表（共 %d 条）:", len(texts))
    for t in texts:
        logger.info("  · %s", t)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Airtest + Poco 自动化工具集",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "manual"],
        default="auto",
        help=(
            "auto   : 脚本自动启动 / 关闭 App（默认）\n"
            "manual : 手动打开 App 并导航到目标页面后按 Enter 开始抓取"
        ),
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="运行设备连接冒烟测试（不执行抓取）",
    )
    parser.add_argument(
        "--dump",
        action="store_true",
        help="连接设备并 dump 当前 UI 树到 outputs/ui_tree_dump.json",
    )
    args = parser.parse_args()

    if args.test:
        logger.info("模式：设备连接冒烟测试")
        run_connection_test()
    elif args.dump:
        logger.info("模式：UI 树 dump")
        run_dump()
    else:
        logger.info("模式：数据抓取 [launch_mode=%s]", args.mode)
        run_scraper(launch_mode=args.mode)


if __name__ == "__main__":
    main()
