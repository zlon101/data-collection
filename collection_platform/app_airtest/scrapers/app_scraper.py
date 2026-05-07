# scrapers/app_scraper.py
"""
综合实战模板：
  - Airtest 负责 App 启动 / 系统级交互
  - Poco 负责控件树解析 / 文本和属性抓取
  - 结果以结构化字典形式安全存储

支持两种启动模式（通过 launch_mode 参数切换）：
  "auto"   — 由脚本调用 start_app() 自动启动，抓取完毕后自动关闭。
  "manual" — 脚本启动后等待用户手动打开 App 并导航到目标页面，
             按 Enter 后开始抓取，结束后不关闭 App。
"""

import argparse
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal, Optional

from airtest.core.api import (
    connect_device,
    sleep,
    snapshot,
    start_app,
    stop_app,
    wake,
)
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from poco.exceptions import PocoNoSuchNodeException, PocoTargetTimeout

# ── 日志配置 ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── 输出目录 ─────────────────────────────────────────────
from ._path_utils import get_project_root
from common.file_manager import write_json_path
OUTPUT_DIR = get_project_root() / "collection_platform" / "app_airtest" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── 数据模型 ──────────────────────────────────────────────
@dataclass
class ListItemData:
    """单条列表项的数据结构"""
    index: int
    title: str = ""
    subtitle: str = ""
    tag: str = ""
    extra_attrs: dict = field(default_factory=dict)


@dataclass
class PageScrapeResult:
    """单页抓取结果"""
    page_index: int
    items: list[ListItemData] = field(default_factory=list)
    scrape_time: str = ""
    error: Optional[str] = None


# ── 设备初始化 ────────────────────────────────────────────
def init_device(adb_path: str = "/opt/homebrew/bin/adb") -> None:
    """连接设备并唤醒屏幕"""
    import os
    if adb_path and Path(adb_path).is_file():
        os.environ["AIRTEST_ADB_PATH"] = adb_path

    connect_device("Android:///")
    wake()
    logger.info("设备初始化完成")


# ── 安全读取节点数据 ──────────────────────────────────────
def safe_get_text(node, default: str = "") -> str:
    """安全地获取节点文本，不存在或无文本时返回默认值。"""
    try:
        text = node.get_text()
        return text.strip() if text else default
    except PocoNoSuchNodeException:
        logger.debug("节点不存在，返回默认值: %s", default)
        return default
    except Exception as exc:
        logger.warning("get_text 异常: %s", exc)
        return default


def safe_get_attr(node, attr_name: str, default: str = "") -> str:
    """安全地获取节点属性值。"""
    try:
        value = node.attr(attr_name)
        return str(value) if value is not None else default
    except PocoNoSuchNodeException:
        logger.debug("节点不存在，attr=%s 返回默认值", attr_name)
        return default
    except Exception as exc:
        logger.warning("attr(%s) 异常: %s", attr_name, exc)
        return default


# ── 核心抓取逻辑 ──────────────────────────────────────────
def scrape_list_page(poco: AndroidUiautomationPoco) -> list[ListItemData]:
    """
    抓取当前页面的列表数据。
    ----------------------------------------------------------------
    本示例假设页面结构如下（请根据实际 App 修改选择器）：

      RecyclerView / ListView
        └── ListItem (可复用的列表条目容器)
              ├── tv_title        (主标题 TextView)
              ├── tv_subtitle     (副标题 TextView)
              └── tv_tag          (标签 TextView，可选)
    ----------------------------------------------------------------
    """
    items: list[ListItemData] = []

    LIST_CONTAINER_ID = "com.example.app:id/recycler_view"
    ITEM_ID = "com.example.app:id/list_item_container"

    try:
        list_container = poco(LIST_CONTAINER_ID)
        list_container.wait_for_appearance(timeout=15.0)
        logger.info("列表容器已找到: %s", LIST_CONTAINER_ID)
    except PocoTargetTimeout:
        logger.error("等待列表容器超时（15s），当前页面可能未正确加载")
        return items

    raw_nodes = list_container.child(ITEM_ID)
    node_count = len(raw_nodes)
    logger.info("找到 %d 个列表项", node_count)

    for idx in range(node_count):
        try:
            item_node = raw_nodes[idx]

            title = safe_get_text(item_node.child("com.example.app:id/tv_title"))
            subtitle = safe_get_text(item_node.child("com.example.app:id/tv_subtitle"))
            tag = safe_get_text(
                item_node.child("com.example.app:id/tv_tag"),
                default="无标签",
            )
            content_desc = safe_get_attr(item_node, "content-desc")
            is_enabled = safe_get_attr(item_node, "enabled", "true")

            items.append(
                ListItemData(
                    index=idx,
                    title=title,
                    subtitle=subtitle,
                    tag=tag,
                    extra_attrs={
                        "content_desc": content_desc,
                        "enabled": is_enabled,
                    },
                )
            )
            logger.debug(
                "[%d] title=%s | subtitle=%s | tag=%s", idx, title, subtitle, tag
            )

        except PocoNoSuchNodeException:
            logger.warning("[%d] 列表项节点访问失败，已跳过", idx)
        except Exception as exc:
            logger.error("[%d] 未预期异常: %s", idx, exc)

    return items


def scrape_with_pagination(
    poco: AndroidUiautomationPoco,
    max_pages: int = 5,
) -> list[PageScrapeResult]:
    """多页抓取主函数，支持翻页操作。"""
    from datetime import datetime

    all_results: list[PageScrapeResult] = []
    NEXT_PAGE_BTN_ID = "com.example.app:id/btn_next_page"

    for page_idx in range(max_pages):
        logger.info("── 开始抓取第 %d 页 ──", page_idx + 1)

        result = PageScrapeResult(
            page_index=page_idx + 1,
            scrape_time=datetime.now().isoformat(),
        )
        try:
            result.items = scrape_list_page(poco)
        except Exception as exc:
            result.error = str(exc)
            logger.error("第 %d 页抓取异常: %s", page_idx + 1, exc)

        all_results.append(result)
        logger.info("第 %d 页完成，共 %d 条", page_idx + 1, len(result.items))

        if page_idx < max_pages - 1:
            next_btn = poco(NEXT_PAGE_BTN_ID)
            try:
                next_btn.wait_for_appearance(timeout=5.0)
                next_btn.click()
                sleep(1.5)
            except PocoTargetTimeout:
                logger.info("未找到「下一页」按钮，已到达最后一页，停止翻页")
                break

    return all_results


def save_results(
    results: list[PageScrapeResult],
    filename: str = "scraped_data.json",
) -> Path:
    """将抓取结果序列化为 JSON 文件。"""
    output_path = OUTPUT_DIR / filename
    serializable = [asdict(r) for r in results]
    write_json_path(serializable, output_path)
    logger.info("数据已保存至: %s", output_path)
    return output_path


# ── 主入口 ────────────────────────────────────────────────
def main(launch_mode: Literal["auto", "manual"] = "auto") -> None:
    """
    主流程：设备连接 → App 准备 → 数据抓取 → 结果保存。

    Args:
        launch_mode:
            "auto"   — 脚本自动调用 start_app() 启动 App，
                       抓取完毕后调用 stop_app() 关闭。
            "manual" — 脚本启动后打印提示，等待用户手动打开 App
                       并导航到目标页面，按 Enter 后开始抓取，
                       结束后保留 App 在前台（不关闭）。
    """
    # 从配置文件读取包名，避免在此处硬编码
    from config.devices import APP_PACKAGE, APP_COLD_START_WAIT, ADB_PATH

    # 1. 连接设备
    init_device(adb_path=ADB_PATH)

    if launch_mode == "auto":
        # ── 自动模式：脚本负责启动和关闭 App ────────────────
        logger.info("[auto] 正在启动 App: %s", APP_PACKAGE)
        start_app(APP_PACKAGE)
        sleep(APP_COLD_START_WAIT)
        logger.info("[auto] App 启动完成，开始抓取")

    else:
        # ── 手动模式：等待用户自行操作 ────────────────────────
        print()
        print("=" * 55)
        print(f"  [manual] 请手动打开 App（{APP_PACKAGE}）")
        print("  并导航到需要抓取的目标页面，")
        print("  准备就绪后按 Enter 开始抓取...")
        print("=" * 55)
        input()  # 阻塞，直到用户按 Enter
        logger.info("[manual] 用户已确认，开始抓取")

    # 2. 初始化 Poco
    poco = AndroidUiautomationPoco(
        use_airtest_input=True,
        screenshot_each_action=False,
    )

    try:
        # 3. 执行多页数据抓取
        results = scrape_with_pagination(poco, max_pages=3)

        # 4. 保存结果
        output_path = save_results(results)

        total_items = sum(len(r.items) for r in results)
        logger.info("抓取完成！共 %d 页，%d 条数据 → %s",
                    len(results), total_items, output_path)

    except Exception as exc:
        snapshot(filename=str(OUTPUT_DIR / "error_snapshot.jpg"))
        logger.error("主流程异常，截图已保存: %s", exc)
        raise

    finally:
        if launch_mode == "auto":
            # 自动模式才关闭 App，手动模式保持原样
            stop_app(APP_PACKAGE)
            logger.info("[auto] App 已关闭")
        else:
            logger.info("[manual] 抓取结束，App 保持运行")


# ── 直接运行此脚本时的命令行入口 ─────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="App 数据抓取脚本",
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
    args = parser.parse_args()
    main(launch_mode=args.mode)
