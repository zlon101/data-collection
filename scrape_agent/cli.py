import asyncio
import json
import sys
import uuid

from dotenv import load_dotenv
from langgraph.types import Command

from common.logger import log
from scrape_agent.graph import build_graph


def _read_instruction() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()
    return input("请输入采集任务: ").strip()


def _ask_approved() -> bool:
    while True:
        raw = input("试抓结果是否符合预期？确认后将执行完整抓取 [y/n]: ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        log("请输入 y 或 n，不要留空。")


async def run_cli(instruction: str) -> None:
    graph = build_graph()
    thread = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = await graph.ainvoke({"user_instruction": instruction}, thread)

    while True:
        snapshot = await graph.aget_state(thread)
        if not snapshot.next:
            break
        payload = {}
        interrupts = getattr(snapshot, "interrupts", None) or ()
        if interrupts:
            payload = interrupts[0].value
        elif snapshot.tasks:
            task_interrupts = getattr(snapshot.tasks[0], "interrupts", None) or ()
            if task_interrupts:
                payload = task_interrupts[0].value
        if not payload:
            payload = {
                "sample_data": snapshot.values.get("sample_data"),
                "scraper_config": snapshot.values.get("scraper_config"),
            }

        log("当前配置: " + json.dumps(payload.get("scraper_config"), ensure_ascii=False))
        log("试抓样本: " + json.dumps(payload.get("sample_data"), ensure_ascii=False, indent=2))
        approved = _ask_approved()
        result = await graph.ainvoke(Command(resume=approved), thread)

    output = (result or {}).get("output_path") if isinstance(result, dict) else None
    if output:
        log(f"任务结束，数据文件: {output}")
    else:
        log("任务结束。")


def main() -> None:
    load_dotenv()
    instruction = _read_instruction()
    if not instruction:
        log("指令为空，已退出。", level="ERROR")
        sys.exit(1)
    asyncio.run(run_cli(instruction))


if __name__ == "__main__":
    main()
